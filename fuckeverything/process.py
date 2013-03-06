import queue
import subprocess
import logging
import string
import random

_mvars = {"processes": {}}


def _random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(8))


def remove(identity):
    pass


def kill_all():
    for (i, p) in _mvars["processes"].items():
        if p.poll():
            queue.add(i, ["s", "FEClose"])
    for (i, p) in _mvars["processes"].items():
        logging.debug("Waiting on process %s to close...", i)
        p.wait()


def add(cmd, identity=None):
    if not identity:
        identity = _random_ident()
    cmd += ["--identity=%s" % identity]
    try:
        logging.debug("Plugin Process: Running %s", cmd)
        o = subprocess.Popen(cmd)
    except OSError, e:
        logging.warning("Plugin Process did not execute correctly: %s", e.strerror)
        return None
    _mvars["processes"][identity] = o
    return identity
