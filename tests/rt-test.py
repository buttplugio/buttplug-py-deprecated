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

#m.msgtype = "RealTouchCDKString"
g = socket()
g.bind(("localhost", 4506))
g.listen(0)
v = g.accept()[0]
while(1):
    r = v.recv(100)
    print r
    v.send("OK")
    m.msgtype = 9999
    m.value = [r]
    s.send(m.rawData())
    # print "Sent final"

# m.msgtype = 100
# s.send(m.rawData())
# q = s.recv(100)
# mg.addData(q)
# msg2 = g.next()
# print msg2.msgtype
# print msg2.value

s.close()
