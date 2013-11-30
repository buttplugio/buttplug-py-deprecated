from buttplug.core import config
from buttplug.core import queue
from buttplug.core import system
from buttplug.core import utils
from buttplug.core import wsclient
import zmq.green as zmq
import msgpack
import logging

# Name a global one underscore off from a module? Why not.
_zmq = {}
_ws_server = None


def init():
    """Initialize structures and sockets needed to run router."""
    _zmq["context"] = zmq.Context()
    queue.init(_zmq["context"])
    _zmq["router"] = _zmq["context"].socket(zmq.ROUTER)
    _zmq["router"].bind(config.get_value("server_address"))
    _zmq["router"].bind("inproc://ws-queue")
    _zmq["router"].setsockopt(zmq.LINGER, 100)
    _zmq["queue"] = _zmq["context"].socket(zmq.PULL)
    _zmq["queue"].connect(queue.QUEUE_ADDRESS)
    _zmq["poller"] = zmq.Poller()
    _zmq["poller"].register(_zmq["router"], zmq.POLLIN)
    _zmq["poller"].register(_zmq["queue"], zmq.POLLIN)
    if config.get_value("websocket_address") is not "":
        wsclient.init_ws(_zmq["context"])


def msg_loop():
    """Main loop for router system. Handles I/O for communication with clients and
    plugins."""
    try:
        while True:
            # Timeout the poll every so often, otherwise things can get stuck
            socks = dict(_zmq["poller"].poll(timeout=1))

            if _zmq["router"] in socks and socks[_zmq["router"]] == zmq.POLLIN:
                identity = _zmq["router"].recv()
                msg = _zmq["router"].recv()
                try:
                    unpacked_msg = msgpack.unpackb(msg)
                except:
                    logging.warning("Malformed message from " + identity)
                    continue
                system.parse_message(identity, unpacked_msg)

            if _zmq["queue"] in socks and socks[_zmq["queue"]] == zmq.POLLIN:
                identity = _zmq["queue"].recv()
                msg = _zmq["queue"].recv()
                _zmq["router"].send(identity, zmq.SNDMORE)
                _zmq["router"].send(msg)
    except utils.BPGreenletExit:
        pass


def shutdown():
    """Kill all remaining greenlets, close sockets."""
    utils.killjoin_greenlets("plugin")
    utils.killjoin_greenlets("client")
    utils.killjoin_greenlets("main")
    _zmq["router"].close()
    _zmq["queue"].close()
    queue.close()
    _zmq["context"].destroy()
