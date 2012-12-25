#!/opt/homebrew/bin/python
from fetemplates import FEClient
import sys
import msgpack
import argparse
import zmq
import random
import string


class FETestClient(FEClient):
    """
    """

    APP_NAME = "TestClient"
    APP_DESCRIPTION = "Client for testing FE Server capabilities"

    def __init__(self, ):
        """
        """
        super(FETestClient, self).__init__()
        self.add_handlers({"FEServerInfo": self.server_info,
                           "FERegisterClient": self.on_register,
                           "FEDeviceList": self.device_list})

    def on_register(self, msg):
        self.send(["FEServerInfo"])
        self.send(["FEDeviceList"])

    def server_info(self, msg):
        print msg

    def device_list(self, msg):
        print msg


def main():
    """Main function for FE Plugin"""
    c = FETestClient()
    return c.run()


if __name__ == '__main__':
    sys.exit(main())
