from fuckeverything import plugin
from fuckeverything import feinfo
from fuckeverything import queue
from fuckeverything import event
from fuckeverything import utils
from fuckeverything import client
import logging

_msg_table = {}


def close_external(identity):
    if plugin.is_plugin(identity):
        pass
    elif client.is_client(identity):
        pass


def _handle_close(identity, msg):
    close_external(identity)


def _handle_server_info(identity, msg):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    queue.add(identity, ["s", "FEServerInfo", [{"name": "Fuck Everything",
                                                "version": feinfo.SERVER_VERSION,
                                                "date": feinfo.SERVER_DATE}]])
    return True


def _handle_plugin_list(identity, msg):
    queue.add(identity, ["s", "FEPluginList", [{"name": p.plugin_info["name"],
                                                "version": p.plugin_info["version"]}
                                               for p in plugin.plugins_available()]])
    return True


def _handle_device_list(identity, msg):
    queue.add(identity, ["s", "FEDeviceList", plugin._devices])
    return True


_msg_table = {"FEServerInfo": _handle_server_info,
              "FEPluginList": _handle_plugin_list,
              "FEPluginDeviceList": plugin.update_device_list,
              "FEDeviceList": _handle_device_list,
              "FEPluginRegisterCount": plugin.handle_count_plugin,
              "FERegisterClient": client.handle_client,
              "FEClaimDevice": plugin.handle_claim_device,
              "FEClose": _handle_close}


def parse_message(identity, msg):
    if not isinstance(msg, (list, tuple)):
        logging.debug("NOT A LIST: %s", msg)
        return
    if len(msg) is 0:
        logging.debug("NULL LIST")
        return
    msg_address = msg[0]
    msg_type = msg[1]
    logging.debug("New message %s", msg_type)
    # System Message
    if msg_address == "s":
        if msg_type in _msg_table.keys():
            _msg_table[msg_type](identity, msg)
        else:
            event.fire(identity, msg_type)
    # Client/Plugin Comms forwarding
    else:
        plugin.forward_device_msg(identity, msg)
