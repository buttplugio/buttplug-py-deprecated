# Buttplug - server module
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

"""The server represents the external I/O capabilities of BP. It maintains the
core zmq ROUTER socket, receiving from and sending to plugins/clients. The
system is considered to be running as long as the msg_loop() greenlet is alive.

"""

from buttplug.core import config
from buttplug.core import queue
from buttplug.core import system
from buttplug.core import greenlet
from buttplug.core import wsclient
import zmq.green as zmq
import msgpack
import logging

# Name a global one underscore off from a module? Why not.
_zmq = {}
_ws_server = None


def init():
    """Initialize structures and sockets needed to run router.

    """
    _zmq["context"] = zmq.Context()
    queue.init(_zmq["context"])
    _zmq["router"] = _zmq["context"].socket(zmq.ROUTER)
    _zmq["router"].bind(config.get_value("server_address"))
    _zmq["router"].bind("inproc://ws-queue")
    _zmq["router"].setsockopt(zmq.LINGER, 100)
    _zmq["queue"] = _zmq["context"].socket(zmq.PULL)
    _zmq["queue"].connect(queue.QUEUE_ADDRESS)
    _zmq["poller"] = zmq.Poller()
    _zmq["poller"].register(_zmq["router"], zmq.POLLIN)
    _zmq["poller"].register(_zmq["queue"], zmq.POLLIN)
    if config.get_value("websocket_address") is not "":
        wsclient.init_ws(_zmq["context"])


def msg_loop():
    """Main loop for router system. Handles I/O for communication with clients and
    plugins.

    """
    try:
        while True:
            # Timeout the poll every so often, otherwise things can get stuck
            socks = dict(_zmq["poller"].poll(timeout=1))

            if _zmq["router"] in socks and socks[_zmq["router"]] == zmq.POLLIN:
                identity = _zmq["router"].recv()
                msg = _zmq["router"].recv()
                try:
                    unpacked_msg = msgpack.unpackb(msg)
                except:
                    logging.warning("Malformed message from " + identity)
                    continue
                system.parse_message(identity, unpacked_msg)

            if _zmq["queue"] in socks and socks[_zmq["queue"]] == zmq.POLLIN:
                identity = _zmq["queue"].recv()
                msg = _zmq["queue"].recv()
                _zmq["router"].send(identity, zmq.SNDMORE)
                _zmq["router"].send(msg)
    except greenlet.BPGreenletExit:
        pass


def shutdown():
    """Kill all remaining greenlets, close sockets.

    """
    greenlet.killjoin_greenlets("plugin")
    greenlet.killjoin_greenlets("client")
    greenlet.killjoin_greenlets("main")
    _zmq["router"].close()
    _zmq["queue"].close()
    queue.close()
    _zmq["context"].destroy()
