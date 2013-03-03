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


def start():
    """Start server loop"""
    # Bring up logging, fill out configuration values
    logging.basicConfig(level=logging.DEBUG)
    config.init()

    # Start zmq server
    context = zmq.Context()
    queue.init(context)
    socket_router = context.socket(zmq.ROUTER)
    socket_router.bind(config.get_value("server_address"))
    socket_queue = context.socket(zmq.PULL)
    socket_queue.connect(queue.QUEUE_ADDRESS)
    poller = zmq.Poller()
    poller.register(socket_router, zmq.POLLIN)
    poller.register(socket_queue, zmq.POLLIN)

    # Start plugins
    plugin.scan_for_plugins()
    plugin.start_plugin_counts()
    if(logging.getLogger().getEffectiveLevel() == logging.DEBUG):
        logging.debug("Plugins found:")
        logging.debug(plugin.plugins_available())
        for plin in plugin.plugins_available():
            logging.debug(plin)
    plugin.scan_for_devices(True)

    # Run Loop
    try:
        while True:
            socks = dict(poller.poll())

            if socket_router in socks and socks[socket_router] == zmq.POLLIN:
                identity = socket_router.recv()
                msg = socket_router.recv()
                system.parse_message(identity, msgpack.unpackb(msg))

            if socket_queue in socks and socks[socket_queue] == zmq.POLLIN:
                identity = socket_queue.recv()
                msg = socket_queue.recv()
                socket_router.send(identity, zmq.SNDMORE)
                socket_router.send(msg)
    except KeyboardInterrupt:
        socket_router.close()
    process.kill_all()
    event.kill_all()
    utils.gevent_join()
    #gevent.shutdown()
    logging.info("Quitting server...")
