from fuckeverything import device
from fuckeverything import plugin
from fuckeverything import feinfo
import time
import re
import sys


def fe_get_server_info(msg, client):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    return ["FEServerInfo", [{"name": "Fuck Everything",
                              "version": feinfo.SERVER_VERSION,
                              "date": feinfo.SERVER_DATE}]]


def fe_plugin_list(msg, client):
    """
    """
    return ["FEPluginList", [{"name": p.plugin_info["name"],
                              "version": p.plugin_info["version"]}
                             for p in plugin.plugins_available()]]


def fe_device_list(msg, client):
    """
    """
    return ["FEDeviceList", [{"name": d["device_info"]["name"],
                              "id": d["id"]}
                             for d in device.devices_available().values()]]


def fe_device_claim(msg, client):
    """
    """
    pass


def fe_client_info(msg, client):
    """
    """
    client.name = msg.value["name"]
    client.version = msg.value["version"]
    return True


def fe_ping(msg, client):
    """
    """
    client.lastping = time.time()
    return True


def fe_claim_device(msg):
    """
    """
    device_id = msg[0]
    if not device.add_device_claim(device_id, client):
        return False
    return True


def fe_release_device(msg, client):
    """
    """
    pass


#PEP8ize message names
FE_CAP_RE = re.compile('^FE')
FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


def convert_msgname(name):
    s0 = FE_CAP_RE.sub(r'fe', name)
    s1 = FIRST_CAP_RE.sub(r'\1_\2', s0)
    return ALL_CAP_RE.sub(r'\1_\2', s1).lower()


def parse_message(msg):
    # TODO: Stop trusting the user will send a value message name
    func_name = convert_msgname(msg[0])
    if func_name not in dir(sys.modules[__name__]):
        return None
    return func_name(msg)
