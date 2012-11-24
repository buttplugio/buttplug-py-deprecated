from twisted.internet import reactor
from client import ClientFactory

def startLoop():
    """
    """
    reactor.listenTCP(12345, ClientFactory())
    reactor.run()

def stopLoop():
    """
    """
    reactor.stop()

