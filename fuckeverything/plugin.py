import os
import json
import subprocess
import gevent
from fuckeverything import queue
from fuckeverything import config
from fuckeverything import heartbeat

_mvars = {}
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
            if info["name"] in _mvars:
                raise PluginException("Plugin Collision! Two plugins named %s" % info["name"])
            _mvars[info["name"]] = info
            plugin_executable = os.path.join(config.PLUGIN_DIR, i, info["executable"])
            if not os.path.exists(plugin_executable):
                raise PluginException("Cannot find plugin executable: %s" % plugin_executable)
            _mvars[info["name"]]["count_process"] = subprocess.Popen([plugin_executable, "--server_port=%s" % config.SERVER_ADDRESS, "--count"])


def add_count_socket(name, identity):
    _mvars[name]["count_socket_identity"] = identity


def scan_for_devices(respawn):
    for (plugin, pdict) in _mvars.items():
        # Race condition, we may not have registered yet
        if "count_socket_identity" not in pdict:
            continue
        # If we lose our count process, god knows what else has gone wrong. Kill it.
        if not heartbeat.contains(pdict["count_socket_identity"]):
            del _mvars[plugin]
            continue
        queue.add_to_queue(pdict["count_socket_identity"], ["FEDeviceCount"])
    if respawn:
        gevent.spawn_later(1, scan_for_devices, respawn)


def update_device_list(identity, device_list):
    plugin_key = None
    for (key, values) in _mvars.items():
        if values["count_socket_identity"] == identity:
            plugin_key = key
            break
    _mvars[plugin_key]["devices"] = device_list


def get_device_list():
    devices = []
    for (key, value) in _mvars.items():
        if "devices" not in value:
            continue
        for dev in value["devices"]:
            devices.append((key, dev))
    return devices


def plugins_available():
    """
    Return the list of all plugins available on the system
    """
    return _mvars.keys()
