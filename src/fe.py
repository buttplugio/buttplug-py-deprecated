import device
import client
import time
import gevent
from gevent.server import StreamServer

def deviceLoop():
    device.scanForDevices()
    gevent.spawn_later(1, deviceLoop)

def clientLoop():
    client.checkClientPings()
    gevent.spawn_later(1, clientLoop)

def start():
    device.scanForPlugins()
    print "Plugins found:"
    for p in device.pluginsAvailable():
        print p
    print device.scanForDevices()
    print "Starting server..."
    gevent.spawn_later(1, deviceLoop)
    gevent.spawn_later(1, clientLoop)
    s = StreamServer(("localhost", 12345), client.runClient)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass
    print "Quitting server..."

