# Buttplug - util module
# Copyright (c) Kyle Machulis/Nonpolynomial Labs, 2012-2013
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the <ORGANIZATION> nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Utility functions used by BP.

"""

import logging
import gevent.pool
import random
from buttplug.core import event
from buttplug.core import queue
from buttplug.core import config

_pools = {}
_live_greenlets = []


class BPGreenletExit(Exception):
    """Exception passed to gevent.kill() to signal a greenlet to die. All BP
    greenlets should handle this exception at any point where gevent could
    block.

    """
    pass


def random_ident():
    """Generate a random string of letters and digits to use as zmq router
    socket identity

    """
    return ''.join(chr(random.randrange(ord('A'), ord('Z')))
                   for x in range(8))


def killjoin_greenlets(pool):
    """Kill and join all greenlets in a named pool. Usually used for shutdown.

    """
    if pool not in _pools:
        logging.info("Pool %s not in the gevent pools, skipping...", pool)
        return
    try:
        # For some reason even though we tell kill to block, it still times out
        # with a weirdly low timeout value. Therefore, we watch for a timeout
        # exception and wait for a join manually if that happens.
        _pools[pool].kill(timeout=1, block=True, exception=BPGreenletExit)
    except gevent.Timeout:
        logging.warning("Timed out (gevent bug?), cleaning up manually")
        _pools[pool].join()
    del _pools[pool]


def spawn_gevent_func(name, pool, func, *args, **kwargs):
    """Spawn a new greenlet that will run the function specified with args/kwargs.
    Greenlet can also be named and added to a pool.

    """
    if pool not in _pools.keys():
        _pools[pool] = gevent.pool.Group()

    def log_run_func(*args, **kwargs):
        try:
            logging.debug("gevent spawn: %s", name)
            _live_greenlets.append(name)
            func(*args, **kwargs)
            _live_greenlets.remove(name)
            logging.debug("gevent shutdown: %s", name)
        except BPGreenletExit:
            logging.error("%s did not correctly handle BPGreenletExit!", name)

    return _pools[pool].spawn(log_run_func, *args, **kwargs)


_id_greenlet = {}


def add_identity_greenlet(identity, greenlet):
    """Add a pair of identity/greenlet for simple access.

    """
    _id_greenlet[identity] = greenlet


def get_identity_greenlet(identity):
    """Given an identity, return the specified greenlet for it.

    """
    if identity in _id_greenlet.keys():
        return _id_greenlet[identity]
    return None


def remove_identity_greenlet(identity, msg=None, kill_greenlet=True):
    """Given an identity, remove the greenlet attached, possibly also
    killing/joining it.

    """
    if identity not in _id_greenlet.keys():
        logging.warning("Trying to remove non-existent greenlet %s!", identity)
        return
    if kill_greenlet and not _id_greenlet[identity].ready():
        _id_greenlet[identity].kill(timeout=1, block=True,
                                    exception=BPGreenletExit)
    del _id_greenlet[identity]


def _heartbeat(identity, greenlet):
    """Given an identity and its corresponding greenlet, start a heartbeat loop.
    Maintain loop until either greenlet dies or connection does not return a
    BPPing message in a timely manner. If message is not returned, kill
    corresponding greenlet.

    """
    while not greenlet.ready():
        e = event.add(identity, "BPPing")
        queue.add(identity, ["s", "BPPing"])
        try:
            e.get(block=True, timeout=config.get_value("ping_max"))
        except gevent.Timeout:
            logging.info("Identity %s died via heartbeat", identity)
            greenlet.kill()
            return
        except BPGreenletExit:
            logging.debug("Heartbeat for %s exiting...", identity)
            return

        if greenlet.ready():
            logging.debug("Heartbeat for %s exiting...", identity)
            return

        try:
            gevent.sleep(config.get_value("ping_rate"))
        except BPGreenletExit:
            logging.debug("Heartbeat for %s exiting...", identity)
            return


def spawn_heartbeat(identity, greenlet):
    """Start a new heartbeat process."""
    return spawn_gevent_func("heartbeat-%s" % identity, "heartbeat", _heartbeat,
                             identity, greenlet)
