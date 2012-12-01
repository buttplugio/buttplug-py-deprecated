from vstroker import VStrokerDevice
from fuckeverything.device import distributeMessage
from fuckeverything.message import Message
import gevent

plugin_info = { "name" : "VStroker",
                "version" : "1.0",
                "author" : "Kyle Machulis",
                "repo_url" : "http://www.github.com/qdot/libvstroker",
                "product_url" : "http://www.vstroker.com",
                "multiclaim" : True }

def getDeviceList():
    """
    """
    return [{ "name" : plugin_info["name"], "path" : dev } for dev in VStrokerDevice.getDeviceList()]
    
def openDevice(device):
    """
    """
    d = VStrokerDevice()
    if not d.open(device["path"]):
        return None
    return d

def closeDevice(device):
    device.close()

def startLoop(device):
    gevent.spawn(parsedReportLoop, device)

def getRawReport(device):
    data = device.readRawData()
    if data is None:
        return None
    m = Message("VStrokerParsedData", data)
    return m

def getParsedReport(device):
    data = device["device"].getParsedData()
    if data is None:
        return None
    m = Message("VStrokerParsedData", data)
    return m

def parsedReportLoop(device):
    while device["device"].isOpen():
        msg = getParsedReport(device)
        if not msg:
            gevent.sleep(.001)
            continue
        distributeMessage(device, msg)
        gevent.sleep(.001)

def getGenericParsedReport(device):
    return getParsedReport(device)

out_message_list = {"VStrokerRawData" : getRawReport,
                    "VStrokerParsedData" : getParsedReport,
                    "Generic3AxisAccelerometer" : getGenericParsedReport}

def getMessageList():
    return {"in" : [], "out" : out_message_list.keys()}

def parseMessage():
    raise "We should never reach this"
