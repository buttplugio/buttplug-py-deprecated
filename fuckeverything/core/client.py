import logging
import gevent
from buttplug.core import utils
from buttplug.core import plugin
from buttplug.core import queue


def handle_client(identity, msg):
    hb = utils.spawn_heartbeat(identity, gevent.getcurrent())
    utils.add_identity_greenlet(identity, gevent.getcurrent())
    # Let the client know we're aware of it
    queue.add(identity, ["s", "FERegisterClient", True])
    while True:
        try:
            gevent.sleep(1)
        except utils.FEGreenletExit:
            break
    plugin.kill_claims(identity)
    if not hb.ready():
        hb.kill(exception=utils.FEGreenletExit, block=True, timeout=1)
    # Remove ourselves, but don't kill since we're already shutting down
    utils.remove_identity_greenlet(identity, kill_greenlet=False)
    queue.add(identity, ["s", "FEClose"])
    logging.debug("Client keeper %s exiting...", identity)
