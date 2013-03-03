import logging
import gevent.pool

_pool = gevent.pool.Group()

class FEShutdownException(Exception):
    pass


def gevent_join():
    _pool.join()


def gevent_func(func):
    def log_run_func(*args, **kwargs):
        logging.debug("gevent spawn: %s", func.__name__)
        func(*args, **kwargs)
        logging.debug("gevent shutdown: %s", func.__name__)

    def spawn_func(*args, **kwargs):
        _pool.spawn(log_run_func, *args, **kwargs)

    return spawn_func
