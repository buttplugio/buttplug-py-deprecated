from fuckeverything import system
from fuckeverything import device
import uuid
import time
import traceback

_mvars = {"clients": {}}


class ClientInstance(object):
    """Struct for holding client data"""
    def __init__(self, socket, address):
        self.cid = uuid.uuid4()
        self.socket = socket
        self.address = address
        self.devices = {}
        self.name = None
        self.version = None
        self.lastping = time.time()


def send_message(client, msg):
    """Send a message to a specified client"""
    if not client.socket:
        return
    client.socket.send(msg.raw_data())


def run_client(socket, address):
    """Create and maintain client connection"""
    global _mvars
    msggen = message.get_message_generator()
    client = ClientInstance(socket, address)
    _mvars["clients"][client.cid] = client
    try:
        while True:
            data = client.socket.recv(1024)
            if not data:
                break
            rawmsg = msggen.next(data)
            if rawmsg is None:
                print "Continue!"
                continue
            print "MESSAGE %d" % rawmsg.msgtype
            outmsg = system.parse_message(rawmsg, client)
            if outmsg is None:
                for dev in client.devices.values():
                    dev["plugin"].parseMessage(rawmsg, client, dev)
                print "No message handler for type %d" % rawmsg.msgtype
                continue
            if outmsg is False:
                print "ERROR"
                continue
            if outmsg is True:
                continue
            client.socket.send(outmsg.raw_data())
    except:
        print "Internal error: disconnecting client"
        print traceback.print_exc()
    print "Client exiting!"
    client.socket.close()
    client.socket = None
    for dev in client.devices.values():
        device.remove_device_claim(dev, client)
    # Unclaim all devices
    del _mvars["clients"][client.cid]
    return


def get_clients():
    """Return all current clients"""
    return _mvars["clients"]


def check_client_pings():
    """Check to make sure all clients are still connected."""
    for cli in _mvars["clients"]:
        ctime = time.time()
        if ctime - cli.lastping > 2:
            print("Lost connection to client, ending")
            cli.socket.close()
            continue
