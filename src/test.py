from socket import socket
from messages import Message, MessageGenerator

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
m.msgtype = 2
s.send(m.rawData())
q = s.recv(100)
mg.addData(q)
msg2 = g.next()
print msg2.msgtype
print msg2.value

s.close()
