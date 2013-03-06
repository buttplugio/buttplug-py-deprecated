#!/usr/bin/python
from fetemplates import FEClient
import sys
import gevent

class FETestClient(FEClient):
    """
    """

    APP_NAME = "TestClient"
    APP_DESCRIPTION = "Client for testing FE Server capabilities"

    def __init__(self, ):
        """
        """
        super(FETestClient, self).__init__()
        self.device_claim_id = None
        self.add_handlers({"FEServerInfo": self.server_info,
                           "FERegisterClient": self.on_register,
                           "FEClaimDevice": self.on_device_claim,
                           "FEDeviceList": self.device_list,
                           "RawTestMsg": self.raw_test_msg})

    def on_register(self, msg):
        self.send(["s", "FEServerInfo"])
        self.send(["s", "FEDeviceList"])

    def raw_test_msg(self, msg):
        print msg

    def run_device_query(self):
        print "Running device query!"
        self.send([self.device_claim_id, "RawTestMsg", "testing"])
        gevent.spawn_later(1, self.run_device_query)

    def on_device_claim(self, msg):
        print "Claimed!"
        print msg
        self.device_claim_id = msg[2]
        self.run_device_query()

    def server_info(self, msg):
        print msg

    def device_list(self, msg):
        print msg
        self.send(["s", "FEClaimDevice", "123"])


def main():
    """Main function for FE Plugin"""
    c = FETestClient()
    return c.run()


if __name__ == '__main__':
    sys.exit(main())
