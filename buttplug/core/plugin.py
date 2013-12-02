# Buttplug - plugin module
# Copyright (c) Kyle Machulis/Nonpolynomial Labs, 2012-2013
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the <ORGANIZATION> nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""Plugins are how BP accesses and controls outside resources, usually
hardware. Each plugin can run in two different modes:

- Count mode, which just keeps a count of how many of a specific resource are
  attached to the system at the moment

- Claim mode, which connects to a certain device address to deliver messages
  back and forth.

Each plugin runs as a process per mode, so there's a minimum of 1 process per
plugin (the count mode process), plus an additional process per device being
accessed. This keeps per device crashes from bringing down the whole system.

To claim a device, a client begins a claim process. The protocol for this is
outlined in the run_device_plugin() docs.

"""

import os
import json
import gevent
import logging
from gevent import subprocess
from buttplug.core import heartbeat
from buttplug.core import greenlet
from buttplug.core import event
from buttplug.core import queue
from buttplug.core import config


class Plugin(object):
    """The plugin class provides access to various plugin configuration values,
    including the name/version of the plugin, where its executables are, and
    the types of messages it accepts.

    It also acts as the source of truth for plugin configuration format,
    specifying the filename and keys required in the loaded JSON dict.

    """
    PLUGIN_INFO_FILE = "bpplugin.json"
    PLUGIN_REQUIRED_KEYS = [u"name", u"version", u"executable", u"messages"]

    def __init__(self, info, plugin_dir):
        self.plugin_path = os.path.join(config.get_dir("plugin"), plugin_dir)
        self.executable_path = os.path.join(config.get_dir("plugin"),
                                            plugin_dir, info["executable"])
        if not os.path.exists(self.executable_path):
            raise PluginException("Cannot find plugin executable: " +
                                  self.executable_path)
        self.name = info["name"]
        self.version = info["version"]
        self.messages = info["messages"]


_plugins = {}
_devices = {}


class PluginException(Exception):
    """Exceptions having to do with BP plugins"""
    pass


def scan_for_plugins():
    """Look through plugin directory for any directory with a file named
    "bpplugin.json". Fill in an plugin object, and pass to _run_count_plugin to
    handle lifetime.

    """
    for i in os.listdir(config.get_dir("plugin")):
        plugin_file = os.path.join(config.get_dir("plugin"), i,
                                   Plugin.PLUGIN_INFO_FILE)
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
            raise PluginException("Plugin Collision! Two plugins named " +
                                  info["name"])
        greenlet.spawn_gevent_func("run_count_plugin: %s" % info["name"],
                                   "plugin", _run_count_plugin, Plugin(info, i))


def _start_process(cmd, identity):
    """Constructs command line options string and runs a plugin process.

    """
    cmd += ["--identity=%s" % identity]
    logging.info("Starting process %s", cmd)
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except OSError, e:
        logging.warning("Plugin Process did not execute correctly: %s",
                        e.strerror)
        return None
    return proc


def _run_count_plugin(plugin):
    """Runs the count process for a plugin. Constantly polls for list of devices,
    keeping an internal reference of the devices available from the plugin.

    """
    count_identity = greenlet.random_ident()
    e = event.add(count_identity, "BPPluginRegisterCount")
    count_process_cmd = [plugin.executable_path, "--server_port=%s" %
                         config.get_value("server_address"), "--count"]
    count_process = _start_process(count_process_cmd, count_identity)
    if not count_process:
        logging.warning("%s count process unable to start. removing.",
                        plugin.name)
        return

    try:
        e.get(block=True, timeout=1)
    except gevent.Timeout:
        logging.info("%s count process never registered, removing.",
                     plugin.name)
        return
    except greenlet.BPGreenletExit:
        logging.debug("Shutting down count process for %s", plugin.name)
        return
    logging.info("Count process for %s up on identity %s", plugin.name,
                 count_identity)
    greenlet.add_identity_greenlet(count_identity, gevent.getcurrent())
    hb = heartbeat.spawn_heartbeat(count_identity, gevent.getcurrent())
    _plugins[plugin.name] = plugin
    while True:
        queue.add(count_identity, ["s", "BPPluginDeviceList"])
        e = event.add(count_identity, "BPPluginDeviceList")
        try:
            (i, msg) = e.get(block=True, timeout=1)
        except gevent.Timeout:
            logging.info("%s count process timed out, removing.", plugin.name)
            break
        except greenlet.BPGreenletExit:
            logging.debug("Shutting down count process for %s", plugin.name)
            break
        _devices[plugin.name] = msg[2]
        # TODO: Make this a configuration value
        try:
            gevent.sleep(1)
        except greenlet.BPGreenletExit:
            logging.debug("Shutting down count process for %s", plugin.name)
            break

    # Heartbeat may already be dead if we're shutting down, so check first
    if not hb.ready():
        hb.kill(exception=greenlet.BPGreenletExit, block=True, timeout=1)
    # Remove ourselves, but don't kill since we're already shutting down
    greenlet.remove_identity_greenlet(count_identity, kill_greenlet=False)
    # TODO: If a count process goes down, does every associated device go with
    # it?
    del _plugins[plugin.name]
    queue.add(count_identity, ["s", "BPClose"])
    logging.debug("Count process %s for %s exiting...", count_identity,
                  plugin.name)


def plugins_available():
    """Return the list of all plugins available on the system

    """
    return _plugins.values()


_ctd = {}
_dtc = {}


def forward_device_msg(identity, msg):
    """Forwards a message from plugin->client or client->plugin, editing it to take
    out all identifying information. This way, all identity management stays in
    the router, and plugins/clients talk to each other with no actual knowledge
    of who claims/says what.

    """
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

    # Client only know their device's provided address (bus address, bluetooth
    # id, etc...). We resolve that to the plugin's socket identity.
    elif to_alias in _dtc.keys():
        # Plugins don't get to know where things come from. Spooooky.
        new_msg = ["s"] + list(msg[1:])
        to_addr = _ctd[identity][0]
    else:
        logging.warning("No claims between %s and %s!", identity, to_addr)
        return

    logging.debug("Forwarding message %s to %s", new_msg, to_addr)
    queue.add(to_addr, new_msg)


def kill_claims(identity):
    """Kill all plugin claims for a certain client identity. Used when a client
    disconnects from the router."""
    if identity not in _ctd:
        logging.warning("No client %s is known to claim a device!", identity)
        return
    for dev_id in _ctd[identity]:
        g = greenlet.get_identity_greenlet(dev_id)
        if g is None:
            logging.warning("Device %s is not bound to client %s", dev_id,
                            identity)
            continue
        g.kill(exception=greenlet.BPGreenletExit, timeout=1, block=True)


def run_device_plugin(identity, msg):
    """Execute the plugin claim protocol. This happens whenever a client requests
    to claim a resource advertised by a plugin.

    """
    # Figure out the plugin that owns the device we want
    p = None
    dev_id = msg[2]
    for (plugin_name, device_list) in _devices.items():
        if dev_id in device_list:
            p = _plugins[plugin_name]

    if p is None:
        logging.warning("Cannot find device %s, failing claim", dev_id)
        queue.add(identity, ["s", "BPClaimDevice", dev_id, False])
        return

    # See whether we already have a claim on the device
    if dev_id in _dtc.keys():
        logging.warning("Device %s already claimed, failing claim", dev_id)
        queue.add(identity, ["s", "BPClaimDevice", dev_id, False])
        return

    # Client to system: bring up device process.
    #
    # Just name the new plugin process socket identity after the device id,
    # because why not.
    device_process = _start_process([p.executable_path, "--server_port=%s" %
                                     config.get_value("server_address")],
                                    dev_id)
    if not device_process:
        logging.warning("%s device process unable to start. removing.",
                        p.name)
        return

    # Device process to system: Register with known identity
    e = event.add(dev_id, "BPPluginRegisterClaim")
    try:
        # TODO: Make device open timeout a config option
        (i, m) = e.get(timeout=5)
    except greenlet.BPGreenletExit:
        # If we shut down now, just drop
        return
    except gevent.Timeout:
        # If we timeout, fail the claim
        logging.info("Device %s failed to start...", dev_id)
        queue.add(dev_id, ["s", "BPClose"])
        queue.add(identity, ["s", "BPClaimDevice", dev_id, False])
        return

    greenlet.add_identity_greenlet(dev_id, gevent.getcurrent())

    # Add a heartbeat now that the process is up
    hb = heartbeat.spawn_heartbeat(dev_id, gevent.getcurrent())

    # System to device process: Open device
    queue.add(dev_id, ["s", "BPPluginOpenDevice", dev_id])
    e = event.add(dev_id, "BPPluginOpenDevice")
    try:
        (i, m) = e.get()
    except greenlet.BPGreenletExit:
        queue.add(dev_id, ["s", "BPClose"])
        return

    # Device process to system: Open or fail
    if m[3] is False:
        logging.info("Device %s failed to open...", dev_id)
        queue.add(dev_id, ["s", "BPClose"])
        queue.add(identity, ["s", "BPClaimDevice", dev_id, False])
        return

    # System to client: confirm device claim
    queue.add(identity, ["s", "BPClaimDevice", dev_id, True])

    if identity not in _ctd.keys():
        _ctd[identity] = []
    _ctd[identity].append(dev_id)
    if dev_id not in _dtc.keys():
        _dtc[dev_id] = []
    _dtc[dev_id].append(identity)

    while True:
        try:
            gevent.sleep(1)
        except greenlet.BPGreenletExit:
            break

    if not hb.ready():
        hb.kill(exception=greenlet.BPGreenletExit, block=True, timeout=1)

    _ctd[identity].remove(dev_id)
    del _dtc[dev_id]

    # Remove ourselves, but don't kill since we're already shutting down
    greenlet.remove_identity_greenlet(dev_id, kill_greenlet=False)
    queue.add(dev_id, ["s", "BPClose"])
    logging.debug("Device keeper %s exiting...", dev_id)
