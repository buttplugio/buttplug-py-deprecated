# Buttplug - heartbeat module
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

"""Heartbeat functions.

"""

import logging
import gevent.pool
from buttplug.core import event
from buttplug.core import greenlet
from buttplug.core import queue
from buttplug.core import config


def _heartbeat(identity, g):
    """Given an identity and its corresponding g, start a heartbeat loop.
    Maintain loop until either g dies or connection does not return a
    BPPing message in a timely manner. If message is not returned, kill
    corresponding g.

    """
    while not g.ready():
        e = event.add(identity, "BPPing")
        queue.add(identity, ["s", "BPPing"])
        try:
            e.get(block=True, timeout=config.get_value("ping_max"))
        except gevent.Timeout:
            logging.info("Identity %s died via heartbeat", identity)
            g.kill()
            return
        except greenlet.BPGreenletExit:
            logging.debug("Heartbeat for %s exiting...", identity)
            return

        if g.ready():
            logging.debug("Heartbeat for %s exiting...", identity)
            return

        try:
            gevent.sleep(config.get_value("ping_rate"))
        except greenlet.BPGreenletExit:
            logging.debug("Heartbeat for %s exiting...", identity)
            return


def spawn_heartbeat(identity, g):
    """Start a new heartbeat process."""
    return greenlet.spawn_gevent_func("heartbeat-%s" % identity, "heartbeat",
                                      _heartbeat, identity, g)
