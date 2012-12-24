import imp
import sys
import os
from fuckeverything import config

_mvars = {"plugins": []}
MAIN_MODULE = "FuckEverything"


def scan_for_plugins():
    """
    http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
    """
    for i in os.listdir(config.PLUGIN_DIR):
        print i
        location = os.path.join(config.PLUGIN_DIR, i)
        if (not os.path.isdir(location)) or \
           (not MAIN_MODULE + ".py" in os.listdir(location)):
            print "continuing"
            continue
        info = imp.find_module(MAIN_MODULE, [location])
        sys.path.append(location)
        _mvars["plugins"].append(imp.load_module(i + "." + MAIN_MODULE, *info))


def plugins_available():
    """
    Return the list of all plugins available on the system
    """
    return _mvars["plugins"]
