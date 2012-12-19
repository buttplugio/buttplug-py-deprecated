import imp
import os
import sys
import config

_mvars = { "plugins" : [] }

MainModule = "FuckEverything"

def scanForPlugins():
    """
    http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
    """
    for i in os.listdir(config.plugin_dir):
        print i
        location = os.path.join(config.plugin_dir, i)
        if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
            print "continuing"
            continue
        info = imp.find_module(MainModule, [location])
        sys.path.append(location)
        _mvars["plugins"].append(imp.load_module(i + "." + MainModule, *info))

def pluginsAvailable():
    """
    """
    return _mvars["plugins"]

