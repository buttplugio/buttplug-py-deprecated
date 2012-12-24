import msgpack
import struct
import socket


class Message(object):
    """Base structure of communication"""

    def __init__(self, msgtype=-1, value=None):
        """Initialize or create message values on construction"""
        self.msgtype = msgtype
        self.value = value

    def _pack(self):
        """Use msgpack to prepare object for sending"""
        return msgpack.packb([self.msgtype, self.value])

    def raw_data(self):
        """Get full raw data of message for sending"""
        msg = self._pack()
        return struct.pack("H", socket.htons(len(msg))) + msg


def get_message_generator():
    """Hand back a message generator that can be cranked via next calls. Next
    calls take new data.

    """
    data = []
    while True:
        while len(data) < 2:
            data += yield None
        msg = Message()
        (length,) = struct.unpack("H", data[0:2])
        length = socket.ntohs(length)
        data = data[2:]
        while len(data) < length:
            data += yield None
        (msg.msgtype, msg.value) = msgpack.unpackb(data[0:length])
        data = data[length:]
        data += yield msg
