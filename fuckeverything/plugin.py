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
_devices = {}


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


@utils.gevent_func
def get_device_list():
    while True:
        for p in _plugins.values():
            queue.add(p.count_identity, ["s", "FEPluginDeviceList"])
        # Add a bogus messages called PingWait. We should never get a reply to
        # this because we never sent it. It just sits in the event table as a
        # way to do an interruptable sleep before we send our next ping to the
        # client.
        e = event.add("DeviceListWait", "FEPingWait")
        try:
            e.get(block=True, timeout=config.get_value("ping_rate"))
        except gevent.Timeout:
            pass
        except utils.FEShutdownException:
            logging.debug("FE Closing, shutting down")
            break
        event.remove("DeviceListWait", "FEPingWait")


def update_device_list(identity, msg):
    for p in _plugins.values():
        if p.count_identity == identity:
            if p.name in _devices.keys():
                del _devices[p.name]
            _devices[p.name] = msg[2]


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
        e = event.add(identity, "s")
        try:
            (identity, msg) = e.get()
        except utils.FEShutdownException:
            return
        msg_type = msg[0]
        if msg_type == "FEClose":
            logging.debug("Count Plugin %s closing", identity)
            break


_ctd = {}
_dtc = {}


# Forwarding messages: Because providing security we don't even need matters.
# Yup.
def forward_device_msg(identity, msg):
    to_alias = msg[0]
    print _ctd
    print _dtc
    to_addr = None
    new_msg = None
    # TODO: Remove [0], make deal with multiclaims. Someday.

    # Plugins aren't allowed to know who owns them, they just see commands from
    # the system. Therefore they set their "to" address as "c", and we replace
    # it with the correct client identity.
    if to_alias == "c":
        new_msg = [identity] + list(msg[1:])
        to_addr = _dtc[identity][0]

    # Clients, on the other hand, only know their device's provided address (bus
    # address, bluetooth id, etc...). We resolve that to the plugin's socket
    # identity.
    elif to_alias in _dtc.keys():
        # Plugins don't get to know where things come from. Spooooky.
        new_msg = ["s"] + list(msg[1:])
        to_addr = _ctd[identity][0]
    else:
        logging.warning("No claims between %s and %s!", identity, to_addr)
        return

    logging.debug("Forwarding message %s to %s", new_msg, to_addr)
    queue.add(to_addr, new_msg)


@utils.gevent_func
def handle_claim_device(identity=None, msg=None):
    # Figure out the plugin that owns the device we want
    p = None
    dev_id = msg[2]
    for (plugin_name, device_list) in _devices.items():
        if dev_id in device_list:
            p = _plugins[plugin_name]

    if p is None:
        logging.warning("Cannot find device %s, failing claim", dev_id)
        queue.add(identity, ["s", "FEClaimDevice", dev_id, False])
        return

    # Client to system: bring up device process.
    #
    # Just name the new plugin process socket identity after the device id,
    # because why not.
    plugin_id = process.add([p.executable_path, "--server_port=%s" % config.get_value("server_address")], dev_id)
    if plugin_id is None:
        queue.add(identity, ["s", "FEPluginClaimDevice", dev_id, False])

    # Device process to system: Register with known identity
    e = event.add(plugin_id, "FEPluginRegisterClaim")
    try:
        (i, m) = e.get()
    except utils.FEShutdownException:
        return

    # System to device process: Open device
    queue.add(plugin_id, ["s", "FEPluginOpenDevice", dev_id])
    e = event.add(plugin_id, "FEPluginOpenDevice")
    try:
        (i, m) = e.get()
    except utils.FEShutdownException:
        return

    # Device process to system: Open or fail
    if msg[1] is False:
        queue.add(plugin_id, ["s", "FEClose"])
        queue.add(identity, ["s", "FEClaimDevice", dev_id, False])
        return

    # System to client: confirm device claim
    queue.add(identity, ["s", "FEClaimDevice", dev_id, True])

    if identity not in _ctd.keys():
        _ctd[identity] = []
    _ctd[identity].append(dev_id)
    if dev_id not in _dtc.keys():
        _dtc[dev_id] = []
    _dtc[dev_id].append(identity)

@utils.gevent_func
def handle_release_device(identity=None, msg=None):
    # Figure out the identity of the process that owns the device
    p = None
    dev_id = msg[1]

    # Close the process
    queue.add(plugin_id, ["s", "FEClose"])


def is_plugin(identity):
    # TODO: Implement
    return False
