import os
import json
import subprocess
from fuckeverything import config

_mvars = {"plugins": [], "count_processes": []}
PLUGIN_INFO_FILE = "feplugin.json"
PLUGIN_REQUIRED_KEYS = [u"name", u"version", u"executable"]


class PluginException(Exception):
    """Exceptions having to do with FE plugins"""
    pass


def scan_for_plugins():
    """Look through config'd plugin directory for any directory with a file
    called named what we expect from the PLUGIN_INFO_FILE constant

    """
    for i in os.listdir(config.PLUGIN_DIR):
        plugin_file = os.path.join(config.PLUGIN_DIR, i, PLUGIN_INFO_FILE)
        if not os.path.exists(plugin_file):
            continue
        with open(plugin_file) as pfile:
            info = json.load(pfile)
            if not set(PLUGIN_REQUIRED_KEYS).issubset(set(info.keys())):
                raise PluginException("Invalid Plugin")
            _mvars["plugins"].append(info)
            plugin_executable = os.path.join(config.PLUGIN_DIR, i, info["executable"])
            if not os.path.exists(plugin_executable):
                raise PluginException("Cannot find plugin executable: %s" % plugin_executable)
            _mvars["count_processes"].append(subprocess.Popen([plugin_executable, "--server_port=%s" % config.SERVER_ADDRESS]))


def plugins_available():
    """
    Return the list of all plugins available on the system
    """
    return _mvars["plugins"]
