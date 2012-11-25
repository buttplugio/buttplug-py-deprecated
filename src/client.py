from Queue import Queue
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from messages import MessageGenerator
import system

# PEP318 example
def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@singleton
class ClientFactory(Factory):
    """
    """
    def __init__(self):
        self._clients = {}

    def buildProtocol(self, addr):
        return ClientInstance()

    def updateClient(self, addr, name):
        self._clients[addr] = name

    def removeClient(self, addr):
        del self._clients[addr]

class ClientInstance(LineReceiver):
    """
    """
    
    def __init__(self, ):
        """
        """
        self._msgQueue = Queue()
        self._devices = {}
        self.setRawMode()
        self.delimiter = ""
        pass
    
    def rawDataReceived(self, data):
        print "Got some data! %d" % len(data)
        m = MessageGenerator()
        m.addData(data)
        z = m.generate()
        l = z.next()
        if l is None:
            print "No message!"
        else:
            if l.msgtype < 1000:
                m = system.ParseSystemMessage(l)
                if m is None:
                    print "No message handler!"
                self.sendLine(m.rawData())
            print l.msgtype
            print l.value
