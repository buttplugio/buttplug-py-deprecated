import gevent
import logging
import msgpack
from fuckeverything import utils

_mvars = {"_socket_events": {}}
QUEUE_ADDRESS = "inproc://fequeue"


@utils.gevent_func
def _send_event_table():
    while True:
        e = gevent.event.AsyncResult()
        add_event("*", "FESendEventTable", e)
        try:
            e.wait()
        except utils.FEShutdownException:
            return
        # TODO Actually send out our event table


def init_event_manager():
    gevent.spawn(_send_event_table)


def add_event(identity, msgtype, event=None):
    if event is None:
        event = gevent.event.AsyncResult()
    if identity not in _mvars["_socket_events"]:
        _mvars["_socket_events"][identity] = {}
    if msgtype in _mvars["_socket_events"][identity]:
        raise ValueError("Event already set!")
    logging.debug("Queuing event %s for identity %s", msgtype, identity)
    _mvars["_socket_events"][identity][msgtype] = event
    print _mvars
    return event


def fire_event(identity, msgtype):
    if identity not in _mvars["_socket_events"] and msgtype not in _mvars["_socket_events"][identity]:
        raise ValueError("Event not set!")
    logging.debug("Firing event %s for identity %s", msgtype, identity)
    _mvars["_socket_events"][identity][msgtype].set((identity, msgtype))
    remove_event(identity, msgtype)


def kill_events():
    logging.debug("Trying to kill all events")
    print _mvars
    for (identity, types) in _mvars["_socket_events"].items():
        for (msgtype, event) in types.items():
            if event:
                event.set_exception(utils.FEShutdownException())


def remove_event(identity, msgtype):
    del _mvars["_socket_events"][identity][msgtype]
