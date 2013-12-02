# Buttplug - queue module
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

"""Simple queue using a ZMQ PUSH/PULL pair. Allows safe queuing across greenlets
of messages to be sent to outside processes.

While a gevent Queue structure could also be used, using a ZMQ PUSH/PULL pair
allows BP to poll on the queue, making server setup more concise.

"""

import zmq.green as zmq
import msgpack

_mvars = {"_socket_queue": None}
QUEUE_ADDRESS = "inproc://fequeue"


def init(context):
    """Initialize the queue. Only needs to be run at beginning of BP process.

    """
    _mvars["_socket_queue"] = context.socket(zmq.PUSH)
    _mvars["_socket_queue"].bind(QUEUE_ADDRESS)


def add(identity, msg):
    """Add a message to be sent to a certain identity to the queue.

    """
    _mvars["_socket_queue"].send(identity, zmq.SNDMORE)
    _mvars["_socket_queue"].send(msgpack.packb(msg))


def close():
    """Close the queue sockets. Only needs to be run at shutdown of BP process.

    """
    _mvars["_socket_queue"].close()
