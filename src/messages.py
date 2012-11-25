import msgpack
import struct
import socket

# Types
# 0 - system messages
# 1000 - raw messages
# 2000 - aggregate messages
# 10000+ - no mans land. Unofficial messages

class Message(object):
    """
    """
    
    def __init__(self, ):
        """
        """
        self.msgtype = -1
        self.value = None

    def pack(self):
        return msgpack.packb([self.msgtype, self.value])

    def rawData(self):
        """
        """
        m = self.pack()
        l = len(m)
        print "size: %d" % l
        z = struct.pack("H", socket.htons(l)) + m
        print "fsize: %d" % len(z)
        return z

class DeviceMessage(Message):
    """
    """
    
    def __init__(self, index):
        """
        """
        self.index = index
        pass

    def pack(self):
        return msgpack.packb([self.msgtype, self.index, self.value])

class MessageGenerator(object):
    """
    """
    
    def __init__(self, ):
        """
        """
        self._currentData = ""
        print "Data left: %d" % len(self._currentData)
    
    def addData(self, data):
        """
        """
        self._currentData += data

    def generate(self):
        """
        """
        print "Data left: %d" % len(self._currentData)
        while True:
            print "Reset!"
            while len(self._currentData) < 2:
                print "Current data less than 2"
                yield None
            print "Data left: %d" % len(self._currentData)
            msg = Message()
            (length,) = struct.unpack("H", self._currentData[0:2])
            length = socket.ntohs(length)
            print "L: %d" % length
            self._currentData = self._currentData[2:]
            print "Data left: %d" % len(self._currentData)
            while len(self._currentData) < length:
                print "Current data less than %d" % length
                yield None                           
            (msg.msgtype, msg.value) = msgpack.unpackb(self._currentData[0:length])
            self._currentData = self._currentData[length:]
            print "Data left: %d" % len(self._currentData)
            yield msg
