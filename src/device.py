import imp
import os
import sys

PluginFolder = os.path.join(os.getcwd(), "plugins")
MainModule = "FuckEverything"

_mvars = { "plugins" : {}, "devices" : {}, "id" : 0}

def scanForPlugins():
    """
    http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
    """
    for i in os.listdir(PluginFolder):
        location = os.path.join(PluginFolder, i)
        if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
            continue
        info = imp.find_module(MainModule, [location])
        sys.path.append(location)
        _mvars["plugins"][i] = (imp.load_module(MainModule, *info)).getFEPlugin()

def scanForDevices():
    new_devices = {}
    [new_devices.update(dict((hash(frozenset(dev.values())), dev) for dev in p.getDeviceList())) for (name, p) in _mvars["plugins"].items()]
    # Remove devices no longer connected
    dead_keys = _mvars["devices"].viewkeys() - new_devices.viewkeys()
    new_keys = new_devices.viewkeys() - _mvars["devices"].viewkeys()    
    # Add new devices
    for k in dead_keys:
        del _mvars["devices"][k]
    for k in new_keys:
        _mvars["devices"][k] = new_devices[k]
        _mvars["devices"][k]["id"] = _mvars["id"]
        _mvars["id"] += 1
    return _mvars["devices"]

def pluginsAvailable():
    """
    """
    return _mvars["plugins"]

def devicesAvailable():
    """
    """
    return _mvars["devices"]
