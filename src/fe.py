import sys
import DeviceManager
from gevent.server import StreamServer
from client import runClient

def main():
    DeviceManager.scanForPlugins()
    print "Plugins found:"
    for p in DeviceManager.pluginsAvailable():
        print p
    print DeviceManager.scanForDevices()
    print "Starting server..."
    s = StreamServer(("localhost", 12345), runClient)
    s.serve_forever()
    return 0

if __name__ == '__main__':
    sys.exit(main())
