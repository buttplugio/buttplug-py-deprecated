from fuckeverything import queue as fequeue
from fuckeverything import config
import gevent
import time
import logging

_last_update = {}


def contains(identity):
    return identity in _last_update.keys()


def add(identity):
    if contains(identity):
        return
    _last_update[identity] = time.time()


def remove(identity):
    if not contains(identity):
        return
    del _last_update[identity]


def update(identity):
    _last_update[identity] = time.time()


def stop():
    for identity in _last_update.items():
        fequeue.add_to_queue(identity, ["FEClose"])


def run():
    now = time.time()
    for (identity, pingtime) in _last_update.items():
        if now - pingtime > config.PING_MAX:
            logging.debug("identity %s died" % identity)
            remove(identity)
            continue
        fequeue.add_to_queue(identity, ["FEPing"])
    gevent.spawn_later(config.PING_RATE, run)
