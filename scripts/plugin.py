#!/opt/homebrew/bin/python
from fetemplates import FEPlugin
import sys
import msgpack
import argparse
import zmq
import random
import string


class TestPlugin(FEPlugin):
    APP_NAME = "Test Plugin"
    APP_DESC = "Test for FE Server Plugin System"

    def __init__(self):
        super(TestPlugin, self).__init__()
        self.add_handlers({"FEDeviceCount": self.get_device_list,
                           "RawTestMsg": self.raw_test_msg})

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
