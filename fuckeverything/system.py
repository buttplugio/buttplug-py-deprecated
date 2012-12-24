from fuckeverything.message import Message
from fuckeverything import device
from fuckeverything import plugin
from fuckeverything import feinfo
import time


def fe_server_info(msg, client):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    return Message(0, [{"name": "Fuck Everything",
                        "version": feinfo.SERVER_VERSION,
                        "date": feinfo.SERVER_DATE}])


def fe_plugin_list(msg, client):
    """
    """
    return Message(1, [{"name": p.plugin_info["name"],
                        "version": p.plugin_info["version"]}
                       for p in plugin.plugins_available()])


def fe_device_list(msg, client):
    """
    """
    return Message(100, [{"name": d["device_info"]["name"],
                          "id": d["id"]}
                         for d in device.devices_available().values()])


def fe_device_addition(msg, client):
    """
    """
    return Message(101, None)


def fe_device_removal(msg, client):
    """
    """
    return Message(102, None)


def fe_device_claim(msg, client):
    """
    """
    return Message(103, None)


def fe_client_info(msg, client):
    """
    """
    client.name = msg.value["name"]
    client.version = msg.value["version"]
    return True


def fe_client_ping(msg, client):
    """
    """
    client.lastping = time.time()
    return True


def fe_plugin_ping(msg, client):
    """
    """
    return True


def fe_client_claim_device(msg, client):
    """
    """
    device_id = msg[0]
    if not device.add_device_claim(device_id, client):
        return False
    return True


def fe_client_release_device(msg, client):
    """
    """
    pass


_MSG_TYPE_DICT = {
    "FEServerInfo": fe_server_info,
    "FEPluginList": fe_plugin_list,
    "FEPluginPing": fe_plugin_ping,
    "FEDeviceList": fe_device_list,
    "FEDeviceAddition": fe_device_addition,
    "FEDeviceRemoval": fe_device_removal,
    "FEDeviceClaim": fe_device_claim,
    "FEClientInfo": fe_client_info,
    "FEClientPing": fe_client_ping,
    "FEClientClaimDevice": fe_client_claim_device,
    "FEClientReleaseDevice": fe_client_release_device
}


def parse_message(msg, client):
    if msg.msgtype not in _MSG_TYPE_DICT.keys():
        return None
    return _MSG_TYPE_DICT[msg.msgtype](msg.value, client)
