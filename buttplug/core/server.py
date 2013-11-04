from buttplug.core import config
from buttplug.core import queue
from buttplug.core import system
from buttplug.core import utils
from buttplug.core import wsclient
import zmq.green as zmq
import msgpack
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

# Name a global one underscore off from a module? Why not.
_zmq = {}
_ws_server = None


def init():
    _zmq["context"] = zmq.Context()
    queue.init(_zmq["context"])
    _zmq["router"] = _zmq["context"].socket(zmq.ROUTER)
    _zmq["router"].bind(config.get_value("server_address"))
    _zmq["router"].setsockopt(zmq.LINGER, 100)
    _zmq["queue"] = _zmq["context"].socket(zmq.PULL)
    _zmq["queue"].connect(queue.QUEUE_ADDRESS)
    _zmq["poller"] = zmq.Poller()
    _zmq["poller"].register(_zmq["router"], zmq.POLLIN)
    _zmq["poller"].register(_zmq["queue"], zmq.POLLIN)
    init_ws()


def init_ws():
    _ws_server = WSGIServer(('', 9390),
                            wsclient.WebSocketClient(_zmq["context"]),
                            handler_class=WebSocketHandler)
    _ws_server.start()

def msg_loop():
    try:
        while True:
            # Timeout the poll every so often, otherwise things can get stuck
            socks = dict(_zmq["poller"].poll(timeout=1))

            if _zmq["router"] in socks and socks[_zmq["router"]] == zmq.POLLIN:
                identity = _zmq["router"].recv()
                msg = _zmq["router"].recv()
                system.parse_message(identity, msgpack.unpackb(msg))

            if _zmq["queue"] in socks and socks[_zmq["queue"]] == zmq.POLLIN:
                identity = _zmq["queue"].recv()
                msg = _zmq["queue"].recv()
                _zmq["router"].send(identity, zmq.SNDMORE)
                _zmq["router"].send(msg)
    except utils.BPGreenletExit:
        pass


def shutdown():
    utils.killjoin_greenlets("plugin")
    utils.killjoin_greenlets("client")
    utils.killjoin_greenlets("main")
    _zmq["router"].close()
    _zmq["queue"].close()
    queue.close()
    _zmq["context"].destroy()
