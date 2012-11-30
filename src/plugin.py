import imp
import os
import sys

_mvars = { "plugins" : [] }

PluginFolder = os.path.join(os.getcwd(), "plugins")
MainModule = "FuckEverything"

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
        _mvars["plugins"].append(imp.load_module(MainModule, *info).getFEPlugin())

def pluginsAvailable():
    """
    """
    return _mvars["plugins"]

