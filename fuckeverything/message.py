import msgpack
import struct
import socket

class Message(object):
    """
    """

    def __init__(self, msgtype = -1, value = None):
        """
        """
        self.msgtype = msgtype
        self.value = value

    def pack(self):
        return msgpack.packb([self.msgtype, self.value])

    def rawData(self):
        """
        """
        m = self.pack()
        return struct.pack("H", socket.htons(len(m))) + m

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
