from gevent_zeromq import zmq
import logging
import msgpack

_mvars = {"_socket_queue": None}
QUEUE_ADDRESS = "inproc://fequeue"


def start_queue(context):
    _mvars["_socket_queue"] = context.socket(zmq.PUSH)
    _mvars["_socket_queue"].bind(QUEUE_ADDRESS)


def add_to_queue(identity, msg):
    _mvars["_socket_queue"].send(identity, zmq.SNDMORE)
    _mvars["_socket_queue"].send(msgpack.packb(msg))


def close_queue():
    _mvars["_socket_queue"].close()
