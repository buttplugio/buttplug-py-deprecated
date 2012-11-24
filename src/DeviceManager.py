import imp
import os

PluginFolder = os.path.join(os.getcwd(), "plugins")
MainModule = "FuckEverything"

_devices = []

def __init__():
    """
    """
    # Making sure we're still actually an object due to how singleton works
    print "New device manager!"
    pass
    
def scanForPlugins():
    """
    http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
    """
    # plugins = []
    possibleplugins = os.listdir(PluginFolder)
    for i in possibleplugins:
        location = os.path.join(PluginFolder, i)
        if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
            continue
        info = imp.find_module(MainModule, [location])
        _devices.append({"name": i, "info": info})
    return _devices
        
def pluginsAvailable():
    """
    """
    return _devices

