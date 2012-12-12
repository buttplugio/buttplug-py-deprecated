from socket import socket
from message import Message, MessageGenerator
import time

s = socket()
s.connect(("localhost", 12345))
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

while True:
    q = s.recv(100)
    mg.addData(q)
    msg2 = g.next()
    print msg2.msgtype
    print msg2.value
    # m.msgtype = 1001
    # s.send(m.rawData())
    # time.sleep(1)

s.close()
