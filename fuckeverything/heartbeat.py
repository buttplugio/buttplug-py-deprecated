from fuckeverything import queue
from fuckeverything import event
from fuckeverything import config
from fuckeverything.utils import gevent_func, FEShutdownException
import gevent
import time
import logging


@gevent_func
def start(identity):
    while True:
        e = event.add(identity, "FEPing")
        queue.add(identity, ["FEPing"])
        try:
            e.get(block=True, timeout=config.get_value("ping_max"))
        except gevent.Timeout:
            logging.debug("identity %s died", identity)
            break
        except FEShutdownException:
            logging.debug("FE Closing, shutting down")
            return

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
            return
        event.remove(identity, "FEPingWait")
