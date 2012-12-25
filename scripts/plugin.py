#!/opt/homebrew/bin/python
from fetemplates import FEPlugin
import sys


class TestPlugin(FEPlugin):
    APP_NAME = "Test Plugin"
    APP_DESC = "Test for FE Server Plugin System"

    def __init__(self):
        super(TestPlugin, self).__init__()
        self.add_handlers({"FEDeviceCount": self.get_device_list,
                           "FEDeviceClaim": self.device_claim,
                           "FEDeviceRelease": self.device_release,
                           "RawTestMsg": self.raw_test_msg})
        self.device_id = None

    def device_claim(self, msg):
        if msg[1] not in ["123", "456", "789"]:
            print "Cannot claim!"
            msg.append(None)
            self.send(msg)
        self.device_id = msg[1]
        msg.append(self.device_id)
        self.send(msg)

    def device_release(self, msg):
        if self.device_id != msg[1]:
            print "Cannot release!"
            msg.append(None)
            self.send(msg)
        self.device_id = None
        msg.append(self.device_id)
        self.send(msg)

    def get_device_list(self, msg):
        """Returns the device list for the plugin"""
        self.send(["FEDeviceCount", ["123", "456", "789"]])

    def raw_test_msg(self, msg):
        self.send(["RawTestMsg", msg[1].swapcase()])


def main():
    """Main function for FE Plugin"""
    t = TestPlugin()
    return t.run()


if __name__ == '__main__':
    sys.exit(main())
