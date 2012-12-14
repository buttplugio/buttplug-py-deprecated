from realtouch import RealTouchDevice

plugin_info = { "name" : "RealTouch",
                "version" : "1.0",
                "author" : "Kyle Machulis",
                "repo_url" : "http://www.github.com/qdot/librealtouch",
                "product_url" : "http://www.realtouch.com",
                "multiclaim" : False }

def getDeviceList():
    """
    """
    return [{ "name" : plugin_info["name"], "path" : dev } for dev in RealTouchDevice.getDeviceList()]

def openDevice(device):
    """
    """
    d = RealTouchDevice()
    if not d.open(device["path"]):
        print "Open failed!"
        return None
    print "opened!"
    return d

def closeDevice(device):
    device.close()

def startLoop(device):
    pass

def ParseCDKString(msg, device):
    print "Running cdk string"
    print msg.value
    device.runCDKCommand(msg.value[0])
    return True

# TODO: Return some kind of status? Or can we just assume fire and forget is cool?
#
# def ReturnStatus(msg, device):
#     d = device.getReturnValue()
#     msg.msgtype = "RealTouchStatus"
#     msg.value = d[1]

# def GenericReturnStatus(msg, device):
#     pass

# in_message_list = { "RealTouchCDKString" : ParseCDKString }
in_message_list = { 9999 : ParseCDKString }

# out_message_list = { "RealTouchStatus" : ReturnStatus,
#                      "GenericDeviceStatus" : GenericReturnStatus }

def getMessageList():
    return {"in" : in_message_list.keys(), "out" : [] }

def parseMessage(msg, client, device):
    print msg.msgtype
    if msg.msgtype not in in_message_list.keys():
        print "Not a ? Message!"
        return
    return in_message_list[msg.msgtype](msg, device["device"])
