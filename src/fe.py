import sys
import device
import client
import plugin
import gevent
from gevent.server import StreamServer

def deviceLoop():
    device.scanForDevices()
    gevent.spawn_later(1, deviceLoop)

def clientLoop():
    # client.checkClientPings()
    gevent.spawn_later(1, clientLoop)

def start():
    sys.path.append("/home/qdot/code/git-projects/fuck-everything/")
    plugin.scanForPlugins()
    print "Plugins found:"
    print plugin.pluginsAvailable()
    for p in plugin.pluginsAvailable():        
        print p.plugin_info["name"]
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

