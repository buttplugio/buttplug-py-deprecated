import gevent
import logging
import msgpack
from fuckeverything.core import utils

_mvars = {"_socket_events": {}}
QUEUE_ADDRESS = "inproc://fequeue"


@utils.gevent_func("send_event_table")
def _send_event_table():
    while True:
        e = add("s", "FESendEventTable")
        try:
            e.get()
        except utils.FEShutdownException:
            return
        # TODO Actually send out our event table


def init():
    _send_event_table()


def add(identity, msgtype, event=None):
    if event is None:
        event = gevent.event.AsyncResult()
    if identity not in _mvars["_socket_events"]:
        _mvars["_socket_events"][identity] = {}
    if msgtype in _mvars["_socket_events"][identity]:
        raise ValueError("Event already set!")
    logging.debug("Queuing event %s for identity %s", msgtype, identity)
    _mvars["_socket_events"][identity][msgtype] = event
    return event


def fire(identity, msg):
    msgtype = msg[1]
    logging.debug("Event %s for %s", msgtype, identity)
    if identity in _mvars["_socket_events"]:
        if msgtype in _mvars["_socket_events"][identity]:
            logging.debug("Firing event %s for identity %s", msgtype, identity)
            _mvars["_socket_events"][identity][msgtype].set((identity, msg))
            remove(identity, msgtype)
            return
        elif "s" in _mvars["_socket_events"][identity]:
            logging.debug("Firing event %s for identity %s", msgtype, identity)
            _mvars["_socket_events"][identity][msgtype].set((identity, msg))
            remove(identity, msgtype)
            return
    if msgtype in _mvars["_socket_events"]["s"]:
        logging.debug("Firing event %s for *", msgtype)
        _mvars["_socket_events"]["s"][msgtype].set((identity, msg))
        remove("s", msgtype)
    else:
        #raise ValueError("Event %s on identity %s not set for any handler!" % (msgtype, identity))
        logging.warning("Event %s on identity %s not set for any handler!" % (msgtype, identity))


def kill_all():
    logging.debug("Trying to kill all events")
    for types in _mvars["_socket_events"].values():
        for event in types.values():
            if event:
                event.set_exception(utils.FEShutdownException())


def remove(identity, msgtype):
    del _mvars["_socket_events"][identity][msgtype]


# def wait_for_msg(msgtype):
#     def wrap(f):
#         def wrapped_f(*args):
#             logging.debug("Adding watch for %s", msgtype)
#             e = add("s", msgtype)
#             try:
#                 (identity, msg) = e.get()
#             except utils.FEShutdownException:
#                 return False
#             return f(identity, msg)
#         return wrapped_f
#     return wrap
