import logging
import gevent
from buttplug.core import util
from buttplug.core import plugin
from buttplug.core import queue


def handle_client(identity, msg):
    """Start a greenlet that will survive the duration of client connection.
    Handles replying to client registration, and cleaning up claims on
    disconnect."""
    hb = util.spawn_heartbeat(identity, gevent.getcurrent())
    util.add_identity_greenlet(identity, gevent.getcurrent())
    # Let the client know we're aware of it
    queue.add(identity, ["s", "BPRegisterClient", True])
    while True:
        try:
            gevent.sleep(1)
        except util.BPGreenletExit:
            break
    plugin.kill_claims(identity)
    if not hb.ready():
        hb.kill(exception=util.BPGreenletExit, block=True, timeout=1)
    # Remove ourselves, but don't kill since we're already shutting down
    util.remove_identity_greenlet(identity, kill_greenlet=False)
    queue.add(identity, ["s", "BPClose"])
    logging.debug("Client keeper %s exiting...", identity)
