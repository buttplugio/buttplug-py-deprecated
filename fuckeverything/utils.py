import logging
import gevent.pool
import random
import string

_pool = gevent.pool.Group()


class FEShutdownException(Exception):
    pass


def random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(8))


def gevent_join():
    _pool.join()


def gevent_func(func):
    def log_run_func(*args, **kwargs):
        logging.debug("gevent spawn: %s", func.__name__)
        func(*args, **kwargs)
        logging.debug("gevent shutdown: %s", func.__name__)

    def spawn_func(*args, **kwargs):
        return _pool.spawn(log_run_func, *args, **kwargs)

    return spawn_func
