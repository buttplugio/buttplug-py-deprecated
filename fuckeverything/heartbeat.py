from fuckeverything import queue as fequeue
from fuckeverything import config
import gevent
import time
import logging


def _run_heartbeat(identity):
    while True:
        e = gevent.event.Event()
        fequeue.add_event(identity, "FEPing", e)
        fequeue.add_to_queue(identity, ["FEPing"])
        ret = e.wait(config.get_config_value("ping_max"))
        if not ret:
            logging.debug("identity %s died", identity)
            break
        gevent.sleep(1)


def start_heartbeat(identity):
    gevent.spawn(_run_heartbeat, identity)
