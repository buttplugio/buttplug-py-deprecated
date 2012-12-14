import socket

s = socket.socket()
s.bind(("localhost", 4506))
s.listen(1)
v = s.accept()[0]
while(1):
    r = v.recv(100)
    print r
    v.send("OK")
