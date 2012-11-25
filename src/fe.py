import sys
import DeviceManager
import client

def main():
    plugins = DeviceManager.scanForPlugins()
    print "Plugins found:"
    for p in plugins:
        print p["name"]
    print "Starting server..."
    client.startLoop()
    return 0

if __name__ == '__main__':
    sys.exit(main())
