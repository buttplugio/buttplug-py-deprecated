import logging
import gevent
from fuckeverything.core import utils
from fuckeverything.core import queue

_clients = []


@utils.gevent_func("client")
def handle_client(identity=None, msg=None):
    _clients.append(identity)
    utils.heartbeat(identity, gevent.getcurrent())
    queue.add(identity, ["s", "FERegisterClient", True])


def is_client(identity):
    # TODO: Implement
    return False
