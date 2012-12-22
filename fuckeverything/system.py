from message import Message
import device
import plugin
import feinfo
import time

def FEServerInfo(msg, client):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    return Message(0, [{"name": "Fuck Everything", "version": feinfo.SERVER_VERSION, "date": feinfo.SERVER_DATE}])

def FEPluginList(msg, client):
    """
    """
    return Message(1, [{"name": p.plugin_info["name"], "version": p.plugin_info["version"]} for p in plugin.pluginsAvailable()])

def FEDeviceList(msg, client):
    """
    """
    return Message(100, [{ "name" : d["device_info"]["name"], "id" : d["id"]} for d in device.devicesAvailable().values()])

def FEDeviceAddition(msg, client):
    """
    """
    return Message(101, None)

def FEDeviceRemoval(msg, client):
    """
    """
    return Message(102, None)

def FEDeviceClaim(msg, client):
    """
    """
    return Message(103, None)

def FEClientInfo(msg, client):
    """
    """
    client.name = msg.value["name"]
    client.version = msg.value["version"]
    return True

def FEClientPing(msg, client):
    """
    """
    client.lastping = time.time()
    return True

def FEPluginPing(msg, client):
    """
    """
    return True

def FEClientClaimDevice(msg, client):
    """
    """
    device_id = msg[0]
    if not device.addDeviceClaim(device_id, client):
        return False
    return True

def FEClientReleaseDevice(msg, client):
    """
    """
    pass

systemMsgTypeDict = {
    "FEServerInfo": FEServerInfo,
    "FEPluginList": FEPluginList,
    "FEPluginPing": FEPluginPing,
    "FEDeviceList": FEDeviceList,
    "FEDeviceAddition": FEDeviceAddition,
    "FEDeviceRemoval": FEDeviceRemoval,
    "FEDeviceClaim": FEDeviceClaim,
    "FEClientInfo": FEClientInfo,
    "FEClientPing": FEClientPing,
    "FEClientClaimDevice": FEClientClaimDevice,
    "FEClientReleaseDevice": FEClientReleaseDevice
}

def ParseMessage(msg, client):
    if msg.msgtype not in systemMsgTypeDict.keys():
        return None
    return systemMsgTypeDict[msg.msgtype](msg.value, client)

