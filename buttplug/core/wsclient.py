from buttplug.core import utils
from buttplug.core import config
import logging
import json
import msgpack
import gevent
import zmq.green as zmq
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler


def init_ws(context):
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
        id = utils.random_ident()
        logging.info("New Websocket connection %s", id)
        utils.spawn_gevent_func("websocket %s" % id, "websockets",
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
        sl = utils.spawn_gevent_func("websocket send %s" % self.identity,
                                     "websockets", WebSocketClient.send_loop,
                                     self)
        rl = utils.spawn_gevent_func("websocket receive %s" % self.identity,
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
