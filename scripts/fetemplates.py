import msgpack
import argparse
import zmq
import random
import string
import time
import gevent


def random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(8))


class FEBase(object):

    APP_NAME = "Default application"
    APP_DESC = "Default description"

    def __init__(self):
        self.socket = None
        self.socket_client = None
        self.exit_now = False
        self.parser = argparse.ArgumentParser()
        self.args = None
        self.server_port = None
        self.last_ping = time.time()
        self.identity = random_ident()
        self.inmsg = {"FEClose": self.close_socket,
                      "FEPing": self.ping_reply}
        self.context = zmq.Context()
        self.socket_queue = self.context.socket(zmq.PUSH)
        self.socket_queue.bind("inproc://fe-%s" % (self.identity))
        self.socket_out = self.context.socket(zmq.PULL)
        self.socket_out.connect("inproc://fe-%s" % (self.identity))
        gevent.spawn_later(2, self.ping_check)

    def ping_check(self):
        if time.time() - self.last_ping > 3:
            print "Dead!"
            self.close_socket()
            return
        gevent.spawn_later(1, self.ping_check)

    def parse_message(self, msg):
        """Parse incoming message"""
        if msg[0] not in self.inmsg.keys():
            print "No handler for %s messages" % msg[0]
            return
        self.inmsg[msg[0]](msg)

    def setup_parser(self):
        self.parser = argparse.ArgumentParser(description=self.APP_DESC)
        self.parser.add_argument('--server_port', metavar='p', type=str, help='port '
                                 'FuckEverything service is listening on', required=True)
        self.add_other_arguments()

    def parse_arguments(self):
        self.args = self.parser.parse_args()

        # We always need a port
        if self.args.server_port is None:
            print "Need argument!"
            return False
        self.server_port = self.args.server_port
        return True

    def add_handlers(self, handlers):
        self.inmsg = dict(self.inmsg.items() + handlers.items())

    def send(self, msg):
        self.socket_queue.send(msgpack.packb(msg))

    def close_socket(self, msg=None):
        self.exit_now = True
        self.send(["FEClose"])

    def ping_reply(self, msg):
        self.last_ping = time.time()
        self.send(msg)

    def add_other_arguments(self):
        pass

    def register(self):
        raise RuntimeError("FEBase should not be used underived!")

    def run(self):
        """deal with network packets until told to quit"""
        self.setup_parser()
        if not self.parse_arguments():
            print "Argument error!"
            return 1
        self.socket_client = self.context.socket(zmq.DEALER)
        self.socket_client.setsockopt(zmq.IDENTITY, random_ident())
        self.socket_client.connect(self.server_port)
        poller = zmq.Poller()
        poller.register(self.socket_client, zmq.POLLIN)
        poller.register(self.socket_out, zmq.POLLIN)

        self.register()

        try:
            while not self.exit_now:
                socks = dict(poller.poll(10))
                if self.socket_client in socks and socks[self.socket_client] == zmq.POLLIN:
                    msg = self.socket_client.recv()
                    self.parse_message(msgpack.unpackb(msg))

                if self.socket_out in socks and socks[self.socket_out] == zmq.POLLIN:
                    msg = self.socket_out.recv()
                    self.socket_client.send(msg)
        except KeyboardInterrupt:
            self.exit_now = True
        self.socket_client.send(msgpack.packb(["FEClose"]))
        self.socket_client.close()
        self.socket_queue.close()
        self.socket_out.close()
        return 0


class FEClient(FEBase):

    def __init__(self):
        super(FEClient, self).__init__()

    def register(self):
        self.send(["FERegisterClient", "Test Client"])


class FEPlugin(FEBase):

    def __init__(self):
        super(FEPlugin, self).__init__()
        self.count_mode = False
        self.device_id = None
        self.add_handlers({"FEDeviceClaim": self.device_claim,
                           "FEDeviceRelease": self.device_release})

    def setup_parser(self):
        super(FEPlugin, self).setup_parser()
        self.parser.add_argument('--count', action='store_true', help='count mode '
                                 "means that process will only be used to keep device "
                                 "counts")

    def get_device_list(self):
        raise RuntimeError("Define your own damn get_device_list!")

    def device_claim(self, msg):
        if msg[1] not in self.get_device_list():
            print "Cannot claim!"
            msglst = list(msg)
            msglst.append(False)
            self.send(msglst)
        self.device_id = msg[1]
        msglst = list(msg)
        msglst.append(True)
        self.send(msglst)

    def device_release(self, msg):
        if self.device_id != msg[1]:
            print "Cannot release!"
            msg.append(None)
            self.send(msg)
        self.device_id = None
        msg.append(self.device_id)
        self.send(msg)
        self.close_socket()

    def parse_arguments(self):
        r = super(FEPlugin, self).parse_arguments()
        if not r:
            return r
        if self.args.count is True:
            self.count_mode = True
        return True

    def register(self):
        self.send(["FERegisterPlugin", self.APP_NAME, self.count_mode])
