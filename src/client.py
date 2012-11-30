from messages import MessageGenerator
from collections import namedtuple
import system
import uuid
import time

_clients = []

ClientInstance = namedtuple("ClientInstance", "id, socket, address, devices, name, version, lastping")

def runClient(socket, address):
    """
    """   
    m = MessageGenerator()
    client = ClientInstance(uuid.uuid4(), socket, address, [], None, None, time.time())
    _clients.append(client)
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
            print "No message handler!"
        client.socket.send(msg.rawData())
        print l.msgtype
        print l.value
        return
    # Unclaim all devices
    _clients.remove(client)
    return

def getClients():
    return _clients
