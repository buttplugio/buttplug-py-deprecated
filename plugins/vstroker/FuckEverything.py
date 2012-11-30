from vstroker import VStrokerDevice

class VStrokerPlugin(object):
    """
    """

    NAME = "VStroker"
    VERSION = "1.0"
    AUTHOR = "Kyle Machulis"
    REPO_URL = "http://www.github.com/qdot/libvstroker"
    PRODUCT_URL = "http://www.vstroker.com"

    def getDeviceList(self, ):
        """
        """
        return [{ "name" : VStrokerPlugin.NAME, "path" : dev } for dev in VStrokerDevice.getDeviceList()]
        
    def getDevice(self, device):
        """
        """
        d = VStrokerDevice()
        d.open_path(device["path"])
        return d

def getFEPlugin():
    return VStrokerPlugin()
