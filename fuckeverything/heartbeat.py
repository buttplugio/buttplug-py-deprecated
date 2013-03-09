from fuckeverything import queue
from fuckeverything import event
from fuckeverything import config
from fuckeverything.utils import gevent_func, FEShutdownException
import gevent
import logging

_removal = []

def _check_removal(identity):
    if identity in _removal:
        _removal.remove(identity)
        return True
    return False


@gevent_func
def start(identity):
    while True:
        if _check_removal(identity):
            return False
        e = event.add(identity, "FEPing")
        queue.add(identity, ["s", "FEPing"])
        try:
            e.get(block=True, timeout=config.get_value("ping_max"))
        except gevent.Timeout:
            if not _check_removal(identity):
                logging.debug("identity %s died", identity)
            return False
        except FEShutdownException:
            logging.debug("FE Closing, shutting down")
            return False

        if _check_removal(identity):
            return False

        # Add a bogus messages called PingWait. We should never get a reply to
        # this because we never sent it. It just sits in the event table as a
        # way to do an interruptable sleep before we send our next ping to the
        # client.
        e = event.add(identity, "FEPingWait")
        try:
            e.get(block=True, timeout=config.get_value("ping_rate"))
        except gevent.Timeout:
            pass
        except FEShutdownException:
            logging.debug("FE Closing, shutting down")
            break
        event.remove(identity, "FEPingWait")


def remove(identity):
    _removal.append(identity)
