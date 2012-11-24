import sys
import DeviceManager
import clientmanager

def main():
    plugins = DeviceManager.scanForPlugins()
    print "Plugins found:"
    for p in plugins:
        print p["name"]
    print "Starting server..."
    clientmanager.startLoop()
    return 0

if __name__ == '__main__':
    sys.exit(main())
