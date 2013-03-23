import queue
import subprocess
import logging
import string
import random
from fuckeverything.core import utils

_mvars = {"processes": {}}


def remove(identity):
    pass


def kill_all(try_close=True):
    if try_close:
        for (i, p) in _mvars["processes"].items():
            if p.poll():
                queue.add(i, ["s", "FEClose"])
        for (i, p) in _mvars["processes"].items():
            logging.debug("Waiting on process %s to close...", i)
            p.wait()
            del _mvars["processes"][i]
    else:
        for (i, p) in _mvars["processes"].items():
            p.kill()
            del _mvars["processes"][i]


def add(cmd, identity=None):
    if not identity:
        identity = utils.random_ident()
    cmd += ["--identity=%s" % identity]
    try:
        logging.debug("Plugin Process: Running %s", cmd)
        o = subprocess.Popen(cmd)
    except OSError, e:
        logging.warning("Plugin Process did not execute correctly: %s", e.strerror)
        return None
    _mvars["processes"][identity] = o
    return identity
