from fuckeverything import queue
from fuckeverything import event
from fuckeverything import config
from fuckeverything.utils import gevent_func, FEShutdownException
import gevent
import time
import logging


@gevent_func
def start_heartbeat(identity):
    while True:
        e = event.add_event(identity, "FEPing")
        queue.add_to_queue(identity, ["FEPing"])
        try:
            e.get(block=True, timeout=config.get_config_value("ping_max"))
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
        e = event.add_event(identity, "FEPingWait")
        try:
            e.get(block=True, timeout=config.get_config_value("ping_rate"))
        except gevent.Timeout:
            pass
        except FEShutdownException:
            logging.debug("FE Closing, shutting down")
            return
        event.remove_event(identity, "FEPingWait")
