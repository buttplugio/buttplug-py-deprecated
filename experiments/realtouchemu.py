import socket

s = socket.socket()
s.bind(("localhost", 4506))
s.listen(0)
v = s.accept()
while True:
    r= v.recv(100)
    print r
    v.send("OK")
