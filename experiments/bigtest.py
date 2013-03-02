import sys
import random
import gevent
import gevent.socket
from message import Message, MessageGenerator

def testClient(num):
    s = gevent.socket.create_connection(("localhost", 12345))
    m = Message()
    mg = MessageGenerator()
    
    # Request server info
    m.msgtype = 0
    s.send(m.rawData())
    q = s.recv(100)
    mg.addData(q)
    g = mg.generate()
    msg2 = g.next()
    print msg2.msgtype
    print msg2.value
    
    # get plugin list
    m.msgtype = 1
    s.send(m.rawData())
    q = s.recv(100)
    mg.addData(q)
    msg2 = g.next()
    print msg2.msgtype
    print msg2.value
    
    # get device list
    m.msgtype = 100
    s.send(m.rawData())
    q = s.recv(100)
    mg.addData(q)
    msg2 = g.next()
    print msg2.msgtype
    print msg2.value
    
    # claim device
    m.msgtype = 1002
    m.value = [0]
    s.send(m.rawData())
    
    iterations = random.randrange(1000, 10000)
    for i in range(0, iterations):
        q = s.recv(100)
        mg.addData(q)
        msg2 = g.next()
        if i % 100 == 0:
            print "%d : %d" % (num, i)
        # print msg2.msgtype
        # print msg2.value
        # m.msgtype = 1001
        # s.send(m.rawData())
        # time.sleep(1)
    s.close()

def main():
    z = []
    for i in range(0, 1000):
        z.append(gevent.spawn(testClient,i))
    gevent.joinall(z)

if __name__ == "__main__":
    sys.exit(main())
