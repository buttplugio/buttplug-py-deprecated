from messages import Message
import DeviceManager
import feinfo

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
    m.value = []
    for (plugin_name, plugin) in DeviceManager.pluginsAvailable().items():
        print plugin
        m.value += { plugin.NAME }

    print m.value
    return m

def DeviceList(msg, client):
    pass

def DeviceAddition(msg, client):
    pass

def DeviceRemoval(msg, client):
    pass

def DeviceClaim(msg, client):
    pass

def ClientInfo(msg, client):
    client.name = msg.value["name"]
    client.version = msg.value["version"]
    return True

def ClientPing(msg, client):
    pass

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


