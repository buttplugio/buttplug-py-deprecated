# Buttplug - event module
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


"""There are times when functions in BP need to wait on information from
an outside source. To do this, they register for an event. Events are keyed
based on the identity of a outside process, and the type of message that those
waiting on the event expect to receive from it. Events can be assigned a
timeout, so that execution can continue if the corresponding message is not
received in the allotted time.

For instance, the heartbeat mechanism uses an event that waits on the BPPing
message from an identity. If the pint message is received, the event fires and
BP considers the outside process to still be alive. If the event times out, the
process is considered to be dead and BP cleans up.

"""

import gevent
import logging

_mvars = {"_socket_events": {}}
QUEUE_ADDRESS = "inproc://fequeue"


def add(identity, msgtype, event=None):
    """Add an event to wait for. An event consists of a message type, and an
    identity we expect to receive the message from.

    """
    if event is None:
        event = gevent.event.AsyncResult()
    if identity not in _mvars["_socket_events"]:
        _mvars["_socket_events"][identity] = {}
    if msgtype in _mvars["_socket_events"][identity]:
        raise ValueError("Event already set!")
    logging.debug("Queuing event %s for identity %s", msgtype, identity)
    _mvars["_socket_events"][identity][msgtype] = event
    return event


def fire(identity, msg):
    """Fire all events related to the message coming from the identity
    specified."""
    msgtype = msg[1]
    se = _mvars["_socket_events"]
    logging.debug("Event %s for %s", msgtype, identity)
    if identity in se:
        if msgtype in se[identity]:
            logging.debug("Firing event %s for identity %s", msgtype, identity)
            se[identity][msgtype].set((identity, msg))
            # If no one is waiting, drop message
            if identity not in se:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            if msgtype not in se[identity]:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            remove(identity, msgtype)
            return
        elif "s" in se[identity]:
            logging.debug("Firing event %s for identity %s", msgtype, identity)
            # If no one is waiting, drop message
            if identity not in se:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            if msgtype not in se[identity]:
                logging.info("No identity waiting on %s for %s, dropping...",
                             msgtype, identity)
                return
            se[identity][msgtype].set((identity, msg))
            remove(identity, msgtype)
            return
    if "s" in se and msgtype in se["s"]:
        logging.debug("Firing event %s for *", msgtype)
        if msgtype not in se["s"]:
            logging.info("No identity waiting on %s for %s, dropping...",
                         msgtype, identity)
            return
        se["s"][msgtype].set((identity, msg))
        remove("s", msgtype)
    else:
        logging.warning("Event %s on identity %s not set for any handler!",
                        msgtype, identity)


def remove(identity, msgtype):
    """Remove an event from the list of things we're waiting on."""
    del _mvars["_socket_events"][identity][msgtype]
