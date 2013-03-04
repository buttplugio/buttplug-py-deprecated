from fuckeverything import plugin
from fuckeverything import feinfo
from fuckeverything import queue
from fuckeverything import event
from fuckeverything import heartbeat
from fuckeverything import utils
import logging


@utils.gevent_func
@event.wait_for_msg("FEServerInfo")
def _handle_server_info(identity=None, msg=None):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    queue.add(identity, ["FEServerInfo", [{"name": "Fuck Everything",
                                           "version": feinfo.SERVER_VERSION,
                                           "date": feinfo.SERVER_DATE}]])
    return True


@utils.gevent_func
@event.wait_for_msg("FEPluginList")
def _handle_plugin_list(identity=None, msg=None):
    queue.add(identity, ["FEPluginList", [{"name": p.plugin_info["name"],
                                           "version": p.plugin_info["version"]}
                                          for p in plugin.plugins_available()]])
    return True


@utils.gevent_func
@event.wait_for_msg("FEDeviceList")
def _handle_device_list(identity=None, msg=None):
    queue.add(identity, ["FEDeviceList", plugin.get_device_list()])
    return True


@utils.gevent_func
@event.wait_for_msg("FEClose")
def _handle_close(identity=None, msg=None):
    logging.info("Identity %s closing", identity)
    return True


def init():
    _handle_device_list()
    _handle_plugin_list()
    _handle_server_info()
    _handle_close()


def parse_message(identity, msg):
    if not isinstance(msg, (list, tuple)):
        logging.debug("NOT A LIST: %s", msg)
        return
    if len(msg) is 0:
        logging.debug("NULL LIST")
        return
    func_name = msg[0]
    logging.debug("New message %s", func_name)
    event.fire(identity, func_name)
