from fuckeverything import config
from fuckeverything import device
from fuckeverything import client
from fuckeverything import plugin
from fuckeverything import queue
from fuckeverything import system
from fuckeverything import heartbeat
from gevent_zeromq import zmq
import time
import gevent
import msgpack


def device_loop():
    """Rescan for devices every second"""
    device.scan_for_devices()
    gevent.spawn_later(1, device_loop)


def server_loop(context):
    socket_router = context.socket(zmq.ROUTER)
    socket_router.bind(config.SERVER_ADDRESS)
    while True:
        gevent.sleep(.1)


def start():
    """Start server loop"""
    config.init_config()
    plugin.scan_for_plugins()
    print "Plugins found:"
    print plugin.plugins_available()
    for plin in plugin.plugins_available():
        print plin["name"]
    # print device.scan_for_devices()
    # print "Starting server..."
    # gevent.spawn_later(1, device_loop)
    heartbeat.run()
    context = zmq.Context()
    #gevent.spawn(server_loop, context)
    queue.start_queue(context)
    socket_router = context.socket(zmq.ROUTER)
    socket_router.bind(config.SERVER_ADDRESS)
    socket_queue = context.socket(zmq.PULL)
    socket_queue.connect(queue.QUEUE_ADDRESS)
    poller = zmq.Poller()
    poller.register(socket_router, zmq.POLLIN)
    poller.register(socket_queue, zmq.POLLIN)
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
    print "Quitting server..."
