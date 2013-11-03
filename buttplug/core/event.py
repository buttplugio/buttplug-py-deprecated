import gevent
import logging

_mvars = {"_socket_events": {}}
QUEUE_ADDRESS = "inproc://fequeue"


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
    se = _mvars["_socket_events"]
    logging.debug("Event %s for %s", msgtype, identity)
    if identity in se:
        if msgtype in se[identity]:
            logging.debug("Firing event %s for identity %s", msgtype, identity)
            se[identity][msgtype].set((identity, msg))
            # If no one is waiting, drop message
            if identity not in se:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            if msgtype not in se[identity]:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            remove(identity, msgtype)
            return
        elif "s" in se[identity]:
            logging.debug("Firing event %s for identity %s", msgtype, identity)
            # If no one is waiting, drop message
            if identity not in se:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            if msgtype not in se[identity]:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            se[identity][msgtype].set((identity, msg))
            remove(identity, msgtype)
            return
    if "s" in se and msgtype in se["s"]:
        logging.debug("Firing event %s for *", msgtype)
        if msgtype not in se["s"]:
            logging.info("No identity waiting on %s for %s, dropping...",
                         msgtype, identity)
            return
        se["s"][msgtype].set((identity, msg))
        remove("s", msgtype)
    else:
        logging.warning("Event %s on identity %s not set for any handler!",
                        msgtype, identity)


def remove(identity, msgtype):
    del _mvars["_socket_events"][identity][msgtype]
