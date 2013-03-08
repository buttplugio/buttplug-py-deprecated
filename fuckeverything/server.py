from fuckeverything import config
from fuckeverything import plugin
from fuckeverything import queue
from fuckeverything import system
from fuckeverything import heartbeat
from fuckeverything import utils
from fuckeverything import event
from fuckeverything import process
from gevent_zeromq import zmq
import msgpack
import logging

# Name a global one underscore off from a module? Why not.
_zmq = {}


def init():
    _zmq["context"] = zmq.Context()
    queue.init(_zmq["context"])
    _zmq["router"] = _zmq["context"].socket(zmq.ROUTER)
    _zmq["router"].bind(config.get_value("server_address"))
    _zmq["queue"] = _zmq["context"].socket(zmq.PULL)
    _zmq["queue"].connect(queue.QUEUE_ADDRESS)
    _zmq["poller"] = zmq.Poller()
    _zmq["poller"].register(_zmq["router"], zmq.POLLIN)
    _zmq["poller"].register(_zmq["queue"], zmq.POLLIN)


def msg_loop():
    socks = dict(_zmq["poller"].poll())

    if _zmq["router"] in socks and socks[_zmq["router"]] == zmq.POLLIN:
        identity = _zmq["router"].recv()
        msg = _zmq["router"].recv()
        system.parse_message(identity, msgpack.unpackb(msg))

    if _zmq["queue"] in socks and socks[_zmq["queue"]] == zmq.POLLIN:
        identity = _zmq["queue"].recv()
        msg = _zmq["queue"].recv()
        _zmq["router"].send(identity, zmq.SNDMORE)
        _zmq["router"].send(msg)


def start():
    """Start server loop"""
    # Bring up logging, fill out configuration values
    logging.basicConfig(level=logging.DEBUG)
    config.init()
    init()

    # Start plugins
    plugin.get_device_list()
    plugin.scan_for_plugins()
    plugin.start_plugin_counts()
    logging.debug("Plugins found:")
    logging.debug(plugin.plugins_available())
    for plin in plugin.plugins_available():
        logging.debug(plin)

    # Run Loop
    try:
        while True:
            msg_loop()
    except KeyboardInterrupt:
        _zmq["router"].close()
    process.kill_all()
    event.kill_all()
    utils.gevent_join()
    logging.info("Quitting server...")
