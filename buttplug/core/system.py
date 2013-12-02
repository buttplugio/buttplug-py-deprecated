# Buttplug - server module
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

"""The system module handles execution of router tasks (setting up new client
connections, sending out plugin info, etc). Messages are passed to it, which it
either identifies as a router task and runs the corresponding function for, or
else passes to the plugin module to be passed to a client or plugin.

"""

from buttplug.core import plugin
from buttplug.core import bpinfo
from buttplug.core import queue
from buttplug.core import event
from buttplug.core import greenlet
from buttplug.core import client
import logging


_msg_table = {}


def _close_internal(identity, msg):
    """Send a kill signal to the greenlet specified by identity. Used for closing
    connections on BPClose messages.

    """
    g = greenlet.get_identity_greenlet(identity)
    if g is not None:
        g.kill(timeout=1, block=True, exception=greenlet.BPGreenletExit)


def _handle_server_info(identity, msg):
    """Server Info

    - Server Name (Changable by user)

    - Server Software Version (static)

    - Server Build Date (static)

    """
    queue.add(identity, ["s", "BPServerInfo",
                         [{"name": "Buttplug",
                           "version": bpinfo.SERVER_VERSION,
                           "date": bpinfo.SERVER_DATE}]])
    return True


def _handle_plugin_list(identity, msg):
    """Handle a request for the list of plugins available to the router.

    """
    queue.add(identity, ["s", "BPPluginList",
                         [{"name": p.name,
                           "version": p.version}
                          for p in plugin.plugins_available()]])
    return True


def _handle_device_list(identity, msg):
    """Handle a request for the list of devices available to router plugins.

    """
    devices = []
    for (k, v) in plugin._devices.items():
        devices.append({"name": k, "devices": v})
    queue.add(identity, ["s", "BPDeviceList", devices])
    return True


def _handle_close(identity, msg):
    """Handle a request to close a connection.
    """
    greenlet.spawn_gevent_func("close and block: %s" % identity,
                               "main", _close_internal,
                               identity, msg)


def _handle_claim_device(identity, msg):
    """Handle a request to claim a device from a plugin.
    """
    greenlet.spawn_gevent_func("claim_device: %s" % msg[2],
                               "device", plugin.run_device_plugin,
                               identity, msg)


def _handle_client(identity, msg):
    """Handle a request to begin a new client connection
    """
    greenlet.spawn_gevent_func("client: %s" % identity,
                               "client", client.handle_client,
                               identity, msg)


def _handle_internals(identity, msg):
    """Handle a request for internal information (greenlets, connections, etc.). To
    be used by dashboard.

    """
    queue.add(identity, ["s", "BPInternals", greenlet._live_greenlets])
    return True


_msg_table = {"BPServerInfo": _handle_server_info,
              "BPPluginList": _handle_plugin_list,
              "BPDeviceList": _handle_device_list,
              "BPRegisterClient": _handle_client,
              "BPClaimDevice": _handle_claim_device,
              "BPInternals": _handle_internals,
              "BPClose": _handle_close}


def parse_message(identity, msg):
    """Given a message from an identity, either execute a function based on the
    message type, or pass to the plugin module to let route to a plugin/client.

    """
    if not isinstance(msg, (list, tuple)):
        logging.warning("Message from %s not a list: %s", identity, msg)
        return
    if len(msg) is 0:
        logging.warning("Null list from %s", identity)
        return
    msg_address = msg[0]
    msg_type = msg[1]
    logging.debug("New message %s from %s", msg_type, identity)
    # System Message
    if msg_address == "s":
        if msg_type in _msg_table.keys():
            _msg_table[msg_type](identity, msg)
        else:
            event.fire(identity, msg)
    else:
        plugin.forward_device_msg(identity, msg)
