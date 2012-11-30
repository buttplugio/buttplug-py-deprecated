from realtouch import RealTouchDevice

class RealTouchPlugin(object):
    """
    """

    NAME = "RealTouch"
    VERSION = "1.0"
    AUTHOR = "Kyle Machulis"
    REPO_URL = "http://www.github.com/qdot/librealtouch"
    PRODUCT_URL = "http://www.realtouch.com"

    def getDeviceList(self, ):
        """
        """
        return [{ "name" : RealTouchPlugin.NAME, "path" : dev } for dev in RealTouchDevice.getDeviceList()]
        
    def getDevice(self, device):
        """
        """
        d = RealTouchDevice()
        d.open_path(device["path"])
        return d

def getFEPlugin():
    return RealTouchPlugin()
