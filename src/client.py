from messages import MessageGenerator, Message
from collections import namedtuple
import system
import uuid
import time

_mvars = {"clients" : []}

ClientInstance = namedtuple("ClientInstance", "id, socket, address, devices, name, version, lastping")

def runClient(socket, address):
    """
    """   
    m = MessageGenerator()
    client = ClientInstance(uuid.uuid4(), socket, address, [], None, None, time.time())
    _mvars["clients"].append(client)
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
        client.socket.send(msg.rawData())
        print l.msgtype
        print l.value
    # Unclaim all devices
    _mvars["clients"].remove(client)
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
        
