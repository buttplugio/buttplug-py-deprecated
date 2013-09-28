import zmq.green as zmq
import logging
import msgpack

_mvars = {"_socket_queue": None}
QUEUE_ADDRESS = "inproc://fequeue"


def init(context):
    _mvars["_socket_queue"] = context.socket(zmq.PUSH)
    _mvars["_socket_queue"].bind(QUEUE_ADDRESS)


def add(identity, msg):
    _mvars["_socket_queue"].send(identity, zmq.SNDMORE)
    _mvars["_socket_queue"].send(msgpack.packb(msg))


def close():
    _mvars["_socket_queue"].close()
