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
        return struct.pack("H", socket.htons(len(m))) + m

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
    
    def addData(self, data):
        """
        """
        self._currentData += data

    def generate(self):
        """
        """
        while True:
            while len(self._currentData) < 2:
                yield None
            msg = Message()
            (length,) = struct.unpack("H", self._currentData[0:2])
            length = socket.ntohs(length)
            self._currentData = self._currentData[2:]
            while len(self._currentData) < length:
                yield None                           
            (msg.msgtype, msg.value) = msgpack.unpackb(self._currentData[0:length])
            self._currentData = self._currentData[length:]
            yield msg
