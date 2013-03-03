from gevent_zeromq import zmq
import logging
import msgpack

_mvars = {"_socket_queue": None, "_socket_events": {}}
QUEUE_ADDRESS = "inproc://fequeue"


def start_queue(context):
    _mvars["_socket_queue"] = context.socket(zmq.PUSH)
    _mvars["_socket_queue"].bind(QUEUE_ADDRESS)


def add_to_queue(identity, msg):
    _mvars["_socket_queue"].send(identity, zmq.SNDMORE)
    _mvars["_socket_queue"].send(msgpack.packb(msg))


def close_queue():
    _mvars["_socket_queue"].close()


def add_event(identity, msgtype, event):
    if identity not in _mvars["_socket_events"]:
        _mvars["_socket_events"][identity] = {}
    if msgtype in _mvars["_socket_events"][identity]:
        raise ValueError("Event already set!")
    logging.debug("Queuing event %s for identity %s", msgtype, identity)
    _mvars["_socket_events"][identity][msgtype] = event


def fire_event(identity, msgtype):
    if identity not in _mvars["_socket_events"] and msgtype not in _mvars["_socket_events"][identity]:
        raise ValueError("Event already set!")
    logging.debug("Firing event %s for identity %s", msgtype, identity)
    _mvars["_socket_events"][identity][msgtype].set()
    del _mvars["_socket_events"][identity][msgtype]
