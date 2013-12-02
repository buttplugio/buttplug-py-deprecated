# Buttplug - websocket module
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

"""Assuming the proper configuration values are set, BP handles websocket
connections directly, allowing developers to write clients/plugins in pure
javascript. The websocket handler maintains the connection to the websocket,
creating a corresponding client connection which it attaches to the ZMQ router.
This allows web developers to ignore the ZMQ requirements of BP while still
using its resources. All messages going through the websocket are encoded to
JSON by the websocket handler.

"""

from buttplug.core import util
from buttplug.core import config
import logging
import json
import msgpack
import gevent
import zmq.green as zmq
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler


def init_ws(context):
    """Initialize websocket connection handler.

    """
    addr = config.get_value("websocket_address")
    logging.info("Opening websocket server on %s", addr)
    # TODO: Believe it or not this is not a valid way to check an address
    _ws_server = WSGIServer(addr,
                            WebSocketClientFactory(context),
                            handler_class=WebSocketHandler)
    _ws_server.start()


class WebSocketClientFactory(object):
    def __init__(self, context):
        self.context = context

    def __call__(self, environ, start_response):
        id = util.random_ident()
        logging.info("New Websocket connection %s", id)
        util.spawn_gevent_func("websocket %s" % id, "websockets",
                               WebSocketClient.run_loop,
                               WebSocketClient(id, self.context, environ)).join()


class WebSocketClient(object):
    def __init__(self, identity, context, environ):
        self.context = context
        self.alive = True
        # Handle websocket connection
        self.ws = environ['wsgi.websocket']
        self.identity = identity
        self.socket_client = None

    def recv_loop(self):
        try:
            while self.alive:
                msg = self.ws.receive()
                json_msg = None
                try:
                    json_msg = json.loads(msg)
                except ValueError:
                    logging.warning("Message from websocket %s not json!",
                                    self.identity)
                    continue
                except:
                    raise
                # for now, msgpack the json we get in
                self.socket_client.send(msgpack.packb(json_msg))
        except:
            self.alive = False
        logging.debug("Exiting Receive Loop for Websocket %s",
                      self.identity)

    def send_loop(self):
        try:
            while self.alive:
                msg = self.socket_client.recv()
                logging.debug("Received Message from Websocket %s",
                              self.identity)
                # unpack and jsonize the message
                json_msg = msgpack.unpackb(msg)
                self.ws.send(json.dumps(json_msg))
        except:
            self.alive = False
        logging.debug("Exiting Send Loop for Websocket %s",
                      self.identity)

    # Each time we get a connection from a websocket, we need to spin off a
    # greenlet that will act as the zmq handler for us. This allows us to just
    # deal with serialization at the JS level, without also having to do zmq
    # setup.
    def run_loop(self):
        # Basically set up a client connection here, complete with normal
        # sockets.
        self.socket_client = self.context.socket(zmq.DEALER)
        self.socket_client.setsockopt(zmq.IDENTITY, self.identity)
        # Hang around for a tiny bit before closing, just to clear out
        self.socket_client.setsockopt(zmq.LINGER, 100)
        self.socket_client.connect("inproc://ws-queue")

        # TODO We should be able to do this in a poll loop, but I can't figure
        # out how to get a pollable fileno from gevent-websocket. The internal
        # socket object just blocks the zmq poller even if set non-block. So,
        # for the moment, we're stuck with using 2 more greenlets. Sadness.
        sl = util.spawn_gevent_func("websocket send %s" % self.identity,
                                    "websockets", WebSocketClient.send_loop,
                                    self)
        rl = util.spawn_gevent_func("websocket receive %s" % self.identity,
                                    "websockets", WebSocketClient.recv_loop,
                                    self)
        try:
            while self.alive:
                gevent.sleep(1)
        except:
            self.alive = False
        self.socket_client.send(msgpack.packb(["s", "BPClose"]))
        sl.join()
        rl.join()
        logging.info("Shutting down Websocket %s", self.identity)
