import os
import json
import gevent
import logging
from fuckeverything import utils
from fuckeverything import heartbeat
from fuckeverything import event
from fuckeverything import queue
from fuckeverything import config
from fuckeverything import process


class Plugin(object):
    PLUGIN_INFO_FILE = "feplugin.json"
    PLUGIN_REQUIRED_KEYS = [u"name", u"version", u"executable", u"messages"]

    def __init__(self, info, plugin_dir):
        self.count_identity = None
        self.plugin_path = os.path.join(config.get_dir("plugin"), plugin_dir)
        self.executable_path = os.path.join(config.get_dir("plugin"), plugin_dir, info["executable"])
        if not os.path.exists(self.executable_path):
            raise PluginException("Cannot find plugin executable: %s" % self.executable_path)
        self.name = info["name"]
        self.version = info["version"]
        self.messages = info["messages"]

    def open_count_process(self):
        count_process_cmd = [self.executable_path, "--server_port=%s" % config.get_value("server_address"), "--count"]
        self.count_identity = process.add(count_process_cmd)
        if not self.count_identity:
            logging.warning("Count process unable to start. Removing plugin from plugin list.")
            del _plugins[self.name]

_plugins = {}


class PluginException(Exception):
    """Exceptions having to do with FE plugins"""
    pass


def scan_for_plugins():
    """Look through config'd plugin directory for any directory with a file
    called named what we expect from the PLUGIN_INFO_FILE constant

    """
    for i in os.listdir(config.get_dir("plugin")):
        plugin_file = os.path.join(config.get_dir("plugin"), i, Plugin.PLUGIN_INFO_FILE)
        if not os.path.exists(plugin_file):
            continue
        info = None
        try:
            with open(plugin_file) as pfile:
                info = json.load(pfile)
        except ValueError:
            logging.warning("JSON configuration not valid for plugin %s!", i)
            continue
        if not set(Plugin.PLUGIN_REQUIRED_KEYS).issubset(set(info.keys())):
            raise PluginException("Invalid Plugin")
        if info["name"] in _plugins.keys():
            raise PluginException("Plugin Collision! Two plugins named %s" % info["name"])
        plugin = Plugin(info, i)
        _plugins[plugin.name] = plugin


def start_plugin_counts():
    for p in _plugins.values():
        p.open_count_process()


def plugins_available():
    """
    Return the list of all plugins available on the system
    """
    return _plugins.keys()


@utils.gevent_func
def handle_count_plugin(identity=None, msg=None):
    heartbeat.start(identity)
    while True:
        e = event.add(identity, "*")
        try:
            (identity, msg) = e.get()
        except utils.FEShutdownException:
            return
        msg_type = msg[0]
        if msg_type == "FEClose":
            logging.debug("Count Plugin %s closing", identity)
            break


@utils.gevent_func
def handle_claim_device(identity=None, msg=None):
    # Figure out the plugin that owns the device we want
    p = None
    dev_id = msg[1]

    # Client to system: bring up device process
    plugin_id = process.add([p.executable_path, "--server_port=%s" % config.get_value("server_address")])
    if plugin_id is None:
        queue.add(identity, ["FEClaimDevice", dev_id, False])

    # Device process to system: Register with known identity
    e = event.add(plugin_id, "FERegisterClaimPlugin")
    try:
        (identity, msg) = e.get()
    except utils.FEShutdownException:
        return

    # System to device process: Open device
    queue.add(plugin_id, ["FEOpenDevice", dev_id])
    e = event.add(plugin_id, "FEOpenDevice")
    try:
        (identity, msg) = e.get()
    except utils.FEShutdownException:
        return

    # Device process to system: Open or fail
    if msg[1] is False:
        queue.add(plugin_id, ["FEClose"])
        queue.add(identity, ["FEClaimDevice", dev_id, False])
        return

    # System to client: confirm device claim
    queue.add(identity, ["FEClaimDevice", dev_id, True])

    # TODO: Update some sort of system tracking for device/client claim!


@utils.gevent_func
def handle_release_device(identity=None, msg=None):
    # Figure out the identity of the process that owns the device
    p = None
    dev_id = msg[1]

    # Close the process
    queue.add(plugin_id, ["FEClose"])


def is_plugin(identity):
    # TODO: Implement
    return False
