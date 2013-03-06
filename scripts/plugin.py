#!/usr/bin/python
from fetemplates import FEPlugin
import sys


class TestPlugin(FEPlugin):
    APP_NAME = "Test Plugin"
    APP_DESC = "Test for FE Server Plugin System"

    def __init__(self):
        super(TestPlugin, self).__init__()
        self.add_handlers({"FEPluginDeviceList": self.send_device_list_msg,
                           "RawTestMsg": self.raw_test_msg})
        self.device_id = None

    def send_device_list_msg(self, msg):
        self.send(["s", "FEPluginDeviceList", self.get_device_list()])

    def get_device_list(self):
        """Returns the device list for the plugin"""
        return ["123", "456", "789"]

    def raw_test_msg(self, msg):
        print "GOT RAW TEST MSG"
        from_addr = msg[0]
        msg_type = msg[1]
        msg_payload = msg[2]
        self.send(["c", "RawTestMsg", msg_payload.swapcase()])

    def open_device(self, msg):
        self.send(["s", "FEPluginOpenDevice", True])


def main():
    """Main function for FE Plugin"""
    t = TestPlugin()
    return t.run()


if __name__ == '__main__':
    sys.exit(main())
