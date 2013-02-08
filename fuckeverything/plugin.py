import os
import json
import subprocess
import gevent
import string
import random
from fuckeverything import queue
from fuckeverything import config
from fuckeverything import heartbeat


def random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(8))


# The claim array holds process information for all claims. It is an array of
# tuples with the following values:
#
# - Client ID(s)
# - Device Bus ID
# - Process ID
# - Plugin Object
#
# Therefore when we get a Device Bus ID addressed message from a client, we can
# use the client ID and bus ID to figure out which socket to route the message
# to. Similarly, when we receive messages from a plugin, we can route to any and
# all client IDs provided with the proper device bus ID.
class Plugin(object):
    PLUGIN_INFO_FILE = "feplugin.json"
    PLUGIN_REQUIRED_KEYS = [u"name", u"version", u"executable"]

    def __init__(self, info, plugin_dir):
        self.count_process = None
        self.count_socket = None
        self.plugin_path = os.path.join(config.PLUGIN_DIR, plugin_dir)
        self.executable_path = os.path.join(config.PLUGIN_DIR, plugin_dir, info["executable"])
        if not os.path.exists(self.executable_path):
            raise PluginException("Cannot find plugin executable: %s" % self.executable_path)
        self.name = info["name"]
        self.version = info["version"]
        self.device_list = []
        self.device_sockets = []
        self.device_processes = {}

    def open_count_process(self):
        self.count_process = subprocess.Popen([self.executable_path, "--server_port=%s" % config.SERVER_ADDRESS, "--count", "--identity=%s" % random_ident()])

_plugins = {}


class PluginException(Exception):
    """Exceptions having to do with FE plugins"""
    pass


def scan_for_plugins():
    """Look through config'd plugin directory for any directory with a file
    called named what we expect from the PLUGIN_INFO_FILE constant

    """
    for i in os.listdir(config.PLUGIN_DIR):
        plugin_file = os.path.join(config.PLUGIN_DIR, i, Plugin.PLUGIN_INFO_FILE)
        if not os.path.exists(plugin_file):
            continue
        info = None
        with open(plugin_file) as pfile:
            info = json.load(pfile)
        if not set(Plugin.PLUGIN_REQUIRED_KEYS).issubset(set(info.keys())):
            raise PluginException("Invalid Plugin")
        if info["name"] in _plugins.keys():
            raise PluginException("Plugin Collision! Two plugins named %s" % info["name"])
        plugin = Plugin(info, i)
        _plugins[plugin.name] = plugin
        plugin.open_count_process()


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


def start_claim_process(name, dev_id):
    if name not in _plugins.keys():
        print "Wrong plugin name!"
        return
    plugin = _plugins[name]
    process_id = random_ident()
    plugin.device_processes[dev_id] = subprocess.Popen([plugin.executable_path, "--server_port=%s" % config.SERVER_ADDRESS, "--identity=%s" % process_id])
    return process_id


# def get_claim_list(name):
#     # TODO: Build a claim list
#     return _plugins[name].claim_queue


def add_device_socket(name, identity):
    _plugins[name].device_sockets.append(identity)


# def get_device_socket(name, identity):
#     _plugins[name].device_sockets.append(identity)
