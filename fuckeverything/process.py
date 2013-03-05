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
            queue.add(i, "FEClose")
    for (i, p) in _mvars["processes"].items():
        logging.debug("Waiting on process %s to close...", i)
        p.wait()


def add(cmd):
    i = _random_ident()
    cmd += ["--identity=%s" % i]
    try:
        logging.debug("Plugin Process: Running %s", cmd)
        o = subprocess.Popen(cmd)
    except OSError, e:
        o = None
        i = None
        logging.warning("Plugin Process did not execute correctly: %s", e.strerror)
        return i
    _mvars["processes"][i] = o
    return i
