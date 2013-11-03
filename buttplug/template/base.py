import msgpack
import argparse
import random
import string
import time
import gevent
import zmq.green as zmq


class BPBase(object):

    APP_NAME = "Default application"
    APP_DESC = "Default description"

    def __init__(self):
        self.socket = None
        self.socket_client = None
        self.exit_now = False
        self.parser = argparse.ArgumentParser()
        self.args = None
        self.socket_identity = None
        self.server_port = None
        self.last_ping = time.time()
        self.identity = self.random_ident()
        self.inmsg = {"BPClose": self.close,
                      "BPPing": self.ping_reply}
        self.context = zmq.Context()
        self.socket_queue = self.context.socket(zmq.PUSH)
        self.socket_queue.bind("inproc://fe-%s" % (self.identity))
        self.socket_out = self.context.socket(zmq.PULL)
        self.socket_out.connect("inproc://fe-%s" % (self.identity))

    def random_ident(self):
        """Generate a random string of letters and digits to use as zmq router
        socket identity

        """
        return ''.join(random.choice(string.ascii_uppercase + string.digits)
                       for x in range(8))

    def ping_check(self):
        if time.time() - self.last_ping > 3:
            print "Server timed out, disconnecting..."
            self.close()
            self.exit_now = True
            return
        gevent.spawn_later(1, self.ping_check)

    def parse_message(self, msg):
        """Parse incoming message"""
        msg_type = msg[1]
        if msg_type in self.inmsg.keys():
            self.inmsg[msg_type](msg)
            return
        print "No handler for %s messages" % msg[1]

    def setup_parser(self):
        self.parser = argparse.ArgumentParser(description=self.APP_DESC)
        self.parser.add_argument('--server_port', metavar='p', type=str, help='port '
                                 'Service is listening on', required=True)
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

    def close(self, msg=None):
        print "Close requested, disconnecting..."
        self.exit_now = True

    def ping_reply(self, msg):
        self.last_ping = time.time()
        self.send(msg)

    def add_other_arguments(self):
        pass

    def register(self):
        raise RuntimeError("Must define own register function!")

    def run(self):
        """deal with network packets until told to quit"""
        self.setup_parser()
        if not self.parse_arguments():
            print "Argument error!"
            return 1
        gevent.spawn_later(2, self.ping_check)
        self.socket_client = self.context.socket(zmq.DEALER)
        self.socket_client.setsockopt(zmq.IDENTITY, self.socket_identity)
        # Hang around for a tiny bit before closing, just to clear out
        self.socket_client.setsockopt(zmq.LINGER, 100)

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
            pass
        self.socket_client.send(msgpack.packb(["s", "BPClose"]))
        self.socket_client.close()
        self.socket_queue.close()
        self.socket_out.close()
        self.context.destroy()
        return 0
