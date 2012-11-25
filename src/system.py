from messages import Message
import DeviceManager
import feinfo

def ServerInfo(v):
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

def PluginList(v):
    """
    """
    m = Message()
    m.msgtype = 1
    
    # PluginList
    # - Array of dicts
    m.value = []
    for plugin in DeviceManager.pluginsAvailable():
        m.value += { plugin["name"] }

    print m.value
    return m

systemMsgTypeDict = {
    0 : ServerInfo,
    # 1 : ClientAppPing,
    2 : PluginList,
    # 100 : DeviceList,
    # 101 : DeviceAddition,
    # 102 : DeviceRemoval,
    # 103 : DeviceClaim,
}

def ParseSystemMessage(msg):
    if msg.msgtype not in systemMsgTypeDict.keys():
        return None
    return systemMsgTypeDict[msg.msgtype](msg.value)


