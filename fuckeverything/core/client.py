import logging
from fuckeverything.core import utils
from fuckeverything.core import queue
from fuckeverything.core import heartbeat

_clients = []


@utils.gevent_func
def handle_client(identity=None, msg=None):
    _clients.append(identity)
    heartbeat.start(identity)
    queue.add(identity, ["s", "FERegisterClient", True])


def is_client(identity):
    # TODO: Implement
    return False
