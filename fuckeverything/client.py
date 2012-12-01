from message import MessageGenerator
import system
import device
import uuid
import time
import traceback

_mvars = {"clients" : {}}

class ClientInstance(object):
    def __init__(self, socket, address):
        self.id = uuid.uuid4()
        self.socket = socket
        self.address = address
        self.devices = {}
        self.name = None
        self.version = None
        self.lastping = time.time()

def sendMessage(client, msg):
    global _mvars
    if not client.socket:
        return
    client.socket.send(msg.rawData())

def runClient(socket, address):
    """
    """
    global _mvars
    m = MessageGenerator()
    client = ClientInstance(socket, address)
    _mvars["clients"][client.id] = client
    try:
        while True:
            data = client.socket.recv(1024)
            if not data:
                break
            m.addData(data)
            z = m.generate()
            l = z.next()
            if l is None:
                continue
            msg = system.ParseMessage(l, client)
            if msg is None:
                print "No message handler for type %d" % l.msgtype
                continue
            if msg is True:
                continue
            client.socket.send(msg.rawData())
    except:
        print "Internal error: disconnecting client"
        print traceback.print_exc()
        pass
    client.socket.close()
    client.socket = None
    for (d_id, d) in client.devices.items():
        device.removeDeviceClaim(d, client)
    # Unclaim all devices
    del _mvars["clients"][client.id]
    return

def getClients():
    return _mvars["clients"]

def checkClientPings():
    for c in _mvars["clients"]:
        t = time.time()
        if t - c.lastping > 2:
            print("Lost connection to client, ending")
            c.socket.close()
            continue

