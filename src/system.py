from messages import Message
import device
import feinfo
import time

def ServerInfo(msg, client):
    """
    """
    m = Message()
    m.msgtype = 0

    # Server Info
    # - Server Name (Changable by user)
    # - Server Software Version (static)
    # - Server Build Date (static)
    m.value = [{"name": "Fuck Everything", "version": feinfo.SERVER_VERSION, "date": feinfo.SERVER_DATE}]
    return m

def PluginList(msg, client):
    """
    """
    m = Message()
    m.msgtype = 1
    
    # PluginList
    # - Array of dicts
    print device.pluginsAvailable()
    m.value = [{"name": p.NAME, "version": p.VERSION} for p in device.pluginsAvailable().values()]
    print m.value
    return m

def DeviceList(msg, client):    
    m = Message()
    m.msgtype = 100
    
    # PluginList
    # - Array of dicts
    m.value = [{ "name" : d["name"], "id" : d["id"]} for d in device.devicesAvailable().values()]
    print m.value
    return m

def DeviceAddition(msg, client):
    m = Message()
    m.msgtype = 101
    return m

def DeviceRemoval(msg, client):
    m = Message()
    m.msgtype = 102
    return m

def DeviceClaim(msg, client):
    pass

def ClientInfo(msg, client):
    client.name = msg.value["name"]
    client.version = msg.value["version"]
    return True

def ClientPing(msg, client):
    client.lastping = time.time()

def ClientClaimDevice(msg, client):
    pass

def ClientReleaseDevice(msg, client):
    pass

systemMsgTypeDict = {
    0 : ServerInfo,
    1 : PluginList,
    100 : DeviceList,
    101 : DeviceAddition,
    102 : DeviceRemoval,
    103 : DeviceClaim,
    1000 : ClientInfo,
    1001 : ClientPing,
    1002 : ClientClaimDevice,
    1003 : ClientReleaseDevice
}

def ParseMessage(msg, client):
    if msg.msgtype not in systemMsgTypeDict.keys():
        return None
    return systemMsgTypeDict[msg.msgtype](msg.value, client)


