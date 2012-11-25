from messages import MessageGenerator
import system
from gevent.server import StreamServer

def Client(socket, address):
    m = MessageGenerator()
    while True:
        data = socket.recv(1024)
        if not data:
            break
        m.addData(data)
        z = m.generate()
        l = z.next()
        if l is None:
            continue
        if l.msgtype < 1000:
            msg = system.ParseSystemMessage(l)
            if msg is None:
                print "No message handler!"
            socket.send(msg.rawData())
            print l.msgtype
            print l.value

def startLoop():
    """
    """
    s = StreamServer(("localhost", 12345), Client)
    s.serve_forever()

def stopLoop():
    """
    """
    pass

