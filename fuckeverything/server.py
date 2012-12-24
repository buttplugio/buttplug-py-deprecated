from fuckeverything import config
from fuckeverything import device
from fuckeverything import client
from fuckeverything import plugin
import gevent
from gevent_zeromq import zmq
from gevent.server import StreamServer


def device_loop():
    """Rescan for devices every second"""
    device.scan_for_devices()
    gevent.spawn_later(1, device_loop)


def client_loop():
    """Ping all active clients every second to make sure they're still alive"""
    # client.check_client_pings()
    gevent.spawn_later(1, client_loop)


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
    # gevent.spawn_later(1, client_loop)
    context = zmq.Context()
    #gevent.spawn(server_loop, context)
    while 1:
        socket_router = context.socket(zmq.ROUTER)
        socket_router.bind(config.SERVER_ADDRESS)
        while True:
            gevent.sleep(.1)
    # svr = StreamServer(("localhost", 12345), client.run_client)
    # try:
    #     svr.serve_forever()
    # except KeyboardInterrupt:
    #     pass
    print "Quitting server..."
