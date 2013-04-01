import logging
import gevent.pool
import random
from gevent import subprocess
from fuckeverything.core import event
from fuckeverything.core import queue
from fuckeverything.core import config

_pool = gevent.pool.Group()
_live_greenlets = []


class FEShutdownException(Exception):
    pass


def random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(chr(random.randrange(ord('A'), ord('Z')))
                   for x in range(8))


def killjoin_greenlets():
    _pool.kill(timeout=1)
    _pool.join()


class gevent_func(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        def log_run_func(*args, **kwargs):
            logging.debug("gevent spawn: %s", func.__name__)
            _live_greenlets.append(self.name)
            func(*args, **kwargs)
            _live_greenlets.remove(self.name)
            logging.debug("gevent shutdown: %s", func.__name__)

        def spawn_func(*args, **kwargs):
            return _pool.spawn(log_run_func, *args, **kwargs)

        return spawn_func


_id_greenlet = {}


def add_identity_greenlet(identity, greenlet):
    _id_greenlet[identity] = greenlet


def remove_identity_greenlet(identity, msg=None):
    if identity not in _id_greenlet.keys():
        logging.warning("Trying to remove identity %s which is not in id-greenlet table!", identity)
        return
    if not _id_greenlet[identity].ready():
        _id_greenlet[identity].kill()
    del _id_greenlet[identity]


@gevent_func("heartbeat")
def heartbeat(identity, greenlet):
    while not greenlet.ready():
        e = event.add(identity, "FEPing")
        queue.add(identity, ["s", "FEPing"])
        try:
            e.get(block=True, timeout=config.get_value("ping_max"))
        except gevent.Timeout:
            logging.info("Identity %s died via heartbeat", identity)
            greenlet.kill()
            return
        except gevent.GreenletExit:
            logging.debug("FE Closing, shutting down")
            return

        if greenlet.ready():
            logging.debug("Greenlet finished!")
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
        except gevent.GreenletExit:
            logging.debug("FE Closing, shutting down")
            return
        event.remove(identity, "FEPingWait")
