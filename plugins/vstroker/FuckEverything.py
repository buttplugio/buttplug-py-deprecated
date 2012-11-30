from vstroker import VStrokerDevice

class VStrokerPlugin(object):
    """
    """

    NAME = "VStroker"
    VERSION = "1.0"
    AUTHOR = "Kyle Machulis"
    REPO_URL = "http://www.github.com/qdot/libvstroker"
    PRODUCT_URL = "http://www.vstroker.com"
    MULTICLAIM = True

    def getDeviceList(self, ):
        """
        """
        return [{ "name" : VStrokerPlugin.NAME, "path" : dev } for dev in VStrokerDevice.getDeviceList()]
        
    def getDevice(self, device):
        """
        """
        d = VStrokerDevice()
        if not d.open(device["path"]):
            return None
        return d

def getFEPlugin():
    return VStrokerPlugin()
