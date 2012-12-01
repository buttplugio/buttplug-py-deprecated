from message import Message
import device
import plugin
import feinfo
import time

def SystemServerInfo(msg, client):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    return Message(0, [{"name": "Fuck Everything", "version": feinfo.SERVER_VERSION, "date": feinfo.SERVER_DATE}])

def SystemPluginList(msg, client):
    """
    """
    return Message(1, [{"name": p.plugin_info["name"], "version": p.plugin_info["version"]} for p in plugin.pluginsAvailable()])

def SystemDeviceList(msg, client):    
    """
    """
    return Message(100, [{ "name" : d["device_info"]["name"], "id" : d["id"]} for d in device.devicesAvailable().values()])

def SystemDeviceAddition(msg, client):
    """
    """
    return Message(101, None)

def SystemDeviceRemoval(msg, client):
    """
    """
    return Message(102, None)

def SystemDeviceClaim(msg, client):
    """
    """
    return Message(103, None)

def ClientInfo(msg, client):
    """
    """
    client.name = msg.value["name"]
    client.version = msg.value["version"]
    return True

def ClientPing(msg, client):
    """
    """
    client.lastping = time.time()
    return True

def ClientClaimDevice(msg, client):
    """
    """
    device_id = msg[0]
    if not device.addDeviceClaim(device_id, client):
        return False
    return True

def ClientReleaseDevice(msg, client):
    """
    """
    pass

systemMsgTypeDict = {
    0 : SystemServerInfo,
    1 : SystemPluginList,
    100 : SystemDeviceList,
    101 : SystemDeviceAddition,
    102 : SystemDeviceRemoval,
    103 : SystemDeviceClaim,
    1000 : ClientInfo,
    1001 : ClientPing,
    1002 : ClientClaimDevice,
    1003 : ClientReleaseDevice
}

def ParseMessage(msg, client):
    if msg.msgtype not in systemMsgTypeDict.keys():
        return None
    return systemMsgTypeDict[msg.msgtype](msg.value, client)


