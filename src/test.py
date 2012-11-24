from socket import socket
from messages import Message

s = socket()
s.connect(("localhost", 12345))
m = Message()
m.msgtype = 1
m.value = [1, 2, 3]
print len(m.rawData())
s.send(m.rawData())
s.close()
