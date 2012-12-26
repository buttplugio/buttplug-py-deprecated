import os
import json
import subprocess
import gevent
from fuckeverything import queue
from fuckeverything import config
from fuckeverything import heartbeat


class Plugin(object):
    def __init__(self, info):
        self.count_process = None
        self.count_socket = None
        self.device_list = []
        self.device_processes = {}
        self.plugin_path = None
        self.executable_path = None
        self.name = info["name"]
        self.version = info["version"]
        self.claim_queue = []

_plugins = {}
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
            if info["name"] in _plugins.keys():
                raise PluginException("Plugin Collision! Two plugins named %s" % info["name"])
            plugin = Plugin(info)
            _plugins[plugin.name] = plugin
            plugin.plugin_path = os.path.join(config.PLUGIN_DIR, i)
            plugin.executable_path = os.path.join(config.PLUGIN_DIR, i, info["executable"])
            if not os.path.exists(plugin.executable_path):
                raise PluginException("Cannot find plugin executable: %s" % plugin.executable_path)
            plugin.count_process = subprocess.Popen([plugin.executable_path, "--server_port=%s" % config.SERVER_ADDRESS, "--count"])


def add_count_socket(name, identity):
    _plugins[name].count_socket = identity


def scan_for_devices(respawn):
    for (pname, pobj) in _plugins.items():
        # Race condition, we may not have registered yet
        if pobj.count_socket is None:
            continue
        # If we lose our count process, god knows what else has gone wrong. Kill it.
        if not heartbeat.contains(pobj.count_socket):
            del _plugins[pname]
            continue
        queue.add_to_queue(pobj.count_socket, ["FEDeviceCount"])
    if respawn:
        gevent.spawn_later(1, scan_for_devices, respawn)


def update_device_list(identity, device_list):
    plugin_key = None
    for (pname, pobj) in _plugins.items():
        if pobj.count_socket == identity:
            plugin_key = pname
            break
    _plugins[plugin_key].device_list = device_list


def start_claim_process(identity, name, dev_id):
    # TODO: Start a process for the plugin requested
    if name not in _plugins.keys():
        print "Wrong plugin name!"
        return
    _plugins[name].claim_queue.append((identity, dev_id))
    _plugins[name].device_processes[dev_id] = subprocess.Popen([_plugins[name]["executable"], "--server_port=%s" % config.SERVER_ADDRESS])


def get_claim_list(name):
    # TODO: Build a claim list
    return _plugins[name].claim_queue


def get_device_list():
    devices = []
    for (pname, pobj) in _plugins.items():
        for dev in pobj.device_list:
            devices.append((pname, dev))
    return devices


def plugins_available():
    """
    Return the list of all plugins available on the system
    """
    return _plugins.keys()
