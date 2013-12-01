# Buttplug - client module
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


"""The client module handles client registration, lifetime, and cleanup. When a
client connected to BP, we create a new greenlet running handle_client, which
makes sure we properly register the client, and clean up all of its device
claims when it is finished.

"""

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
