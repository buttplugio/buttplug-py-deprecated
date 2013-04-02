import logging
import gevent.pool
import random
from gevent import subprocess
from fuckeverything.core import event
from fuckeverything.core import queue
from fuckeverything.core import config

_pools = {}
_live_greenlets = []


class FEGreenletExit(Exception):
    pass


def random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(chr(random.randrange(ord('A'), ord('Z')))
                   for x in range(8))


def killjoin_greenlets(pool):
    if pool not in _pools:
        logging.info("Pool %s not in the gevent pools, skipping...", pool)
        return
    try:
        # For some reason even though we tell kill to block, it still times out
        # with a weirdly low timeout value. Therefore, we watch for a timeout
        # exception and wait for a join manually if that happens.
        _pools[pool].kill(timeout=1, block=True, exception=FEGreenletExit)
    except gevent.Timeout:
        logging.warning("Timed out (gevent bug?), cleaning up manually")
        _pools[pool].join()


class gevent_func(object):
    def __init__(self, name, pool):
        self.name = name
        self.pool = pool
        if self.pool not in _pools.keys():
            _pools[self.pool] = gevent.pool.Group()

    def __call__(self, func):
        def log_run_func(*args, **kwargs):
            logging.debug("gevent spawn: %s", func.__name__)
            _live_greenlets.append(self.name)
            func(*args, **kwargs)
            _live_greenlets.remove(self.name)
            logging.debug("gevent shutdown: %s", func.__name__)

        def spawn_func(*args, **kwargs):
            return _pools[self.pool].spawn(log_run_func, *args, **kwargs)

        return spawn_func


_id_greenlet = {}


def add_identity_greenlet(identity, greenlet):
    _id_greenlet[identity] = greenlet


def get_identity_greenlet(identity):
    if identity in _id_greenlet.keys():
        return _id_greenlet[identity]
    return None


def remove_identity_greenlet(identity, msg=None, kill_greenlet=True):
    if identity not in _id_greenlet.keys():
        logging.warning("Trying to remove identity %s which is not in id-greenlet table!", identity)
        return
    if kill_greenlet and not _id_greenlet[identity].ready():
        _id_greenlet[identity].kill(timeout=1, block=True, exception=FEGreenletExit)
    del _id_greenlet[identity]


@gevent_func("heartbeat", "heartbeat")
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
        except FEGreenletExit:
            logging.debug("Heartbeat for %s exiting...", identity)
            return

        if greenlet.ready():
            logging.debug("Heartbeat for %s exiting...", identity)
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
        except FEGreenletExit:
            logging.debug("Heartbeat for %s exiting...", identity)
            return
        event.remove(identity, "FEPingWait")
