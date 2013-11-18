from buttplug.core import plugin
from buttplug.core import feinfo
from buttplug.core import queue
from buttplug.core import event
from buttplug.core import utils
from buttplug.core import client
import logging


_msg_table = {}


def close_internal(identity, msg):
    g = utils.get_identity_greenlet(identity)
    if g is not None:
        g.kill(timeout=1, block=True, exception=utils.BPGreenletExit)


def _handle_server_info(identity, msg):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    queue.add(identity, ["s", "BPServerInfo",
                         [{"name": "Buttplug",
                           "version": feinfo.SERVER_VERSION,
                           "date": feinfo.SERVER_DATE}]])
    return True


def _handle_plugin_list(identity, msg):
    queue.add(identity, ["s", "BPPluginList",
                         [{"name": p.name,
                           "version": p.version}
                          for p in plugin.plugins_available()]])
    return True


def _handle_device_list(identity, msg):
    devices = []
    for (k, v) in plugin._devices.items():
        devices.append({"name": k, "devices": v})
    queue.add(identity, ["s", "BPDeviceList", devices])
    return True


def _handle_close(identity, msg):
    utils.spawn_gevent_func("close and block: %s" % identity,
                            "main", close_internal,
                            identity, msg)


def _handle_claim_device(identity, msg):
    utils.spawn_gevent_func("claim_device: %s" % msg[2],
                            "device", plugin.run_device_plugin,
                            identity, msg)


def _handle_client(identity, msg):
    utils.spawn_gevent_func("client: %s" % identity,
                            "client", client.handle_client,
                            identity, msg)


_msg_table = {"BPServerInfo": _handle_server_info,
              "BPPluginList": _handle_plugin_list,
              "BPDeviceList": _handle_device_list,
              "BPRegisterClient": _handle_client,
              "BPClaimDevice": _handle_claim_device,
              "BPClose": _handle_close}


def parse_message(identity, msg):
    if not isinstance(msg, (list, tuple)):
        logging.warning("Message from %s not a list: %s", identity, msg)
        return
    if len(msg) is 0:
        logging.warning("Null list from %s", identity)
        return
    msg_address = msg[0]
    msg_type = msg[1]
    # if msg_type not in ["BPPing", "BPPluginDeviceList"]:
    logging.info("New message %s from %s", msg_type, identity)
    # System Message
    if msg_address == "s":
        if msg_type in _msg_table.keys():
            _msg_table[msg_type](identity, msg)
        else:
            event.fire(identity, msg)
    # Client/Plugin Comms forwarding
    else:
        plugin.forward_device_msg(identity, msg)
