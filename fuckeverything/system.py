from fuckeverything import plugin
from fuckeverything import feinfo
from fuckeverything import queue
from fuckeverything import event
from fuckeverything import heartbeat
import logging
import re
import sys


class Claim(object):
    """
    """

    def __init__(self, device_address, client_id, device_process_id):
        """
        """
        self.device_address = device_address
        self.client_id = client_id
        self.device_process_id = device_process_id


_claims = []


def find_claim(device_address=None, client_id=None, device_process_id=None):
    if device_address is not None:
        for c in _claims:
            if c.device_address == device_address:
                return c
    elif client_id is not None:
        for c in _claims:
            if c.client_id == client_id:
                return c
    elif device_process_id is not None:
        for c in _claims:
            if c.device_process_id == device_process_id:
                return c
    return None


def fe_server_info(identity, msg):
    """
    Server Info
    - Server Name (Changable by user)
    - Server Software Version (static)
    - Server Build Date (static)
    """
    queue.add_to_queue(identity, ["FEServerInfo", [{"name": "Fuck Everything",
                                                    "version": feinfo.SERVER_VERSION,
                                                    "date": feinfo.SERVER_DATE}]])


def fe_plugin_list(identity, msg):
    """
    """
    queue.add_to_queue(identity, ["FEPluginList", [{"name": p.plugin_info["name"],
                                                    "version": p.plugin_info["version"]}
                                                   for p in plugin.plugins_available()]])


def fe_device_list(identity, msg):
    """
    """
    queue.add_to_queue(identity, ["FEDeviceList", plugin.get_device_list()])


def fe_device_count(identity, msg):
    """
    """
    logging.debug("%s got device list %s", identity, msg[1])
    plugin.update_device_list(identity, msg[1])


def fe_device_claim(identity, msg):
    """
    """
    (plugin_name, device_id, claim_result) = msg[1:]
    c = find_claim(device_process_id=identity)
    if c is None:
        raise RuntimeError("Cannot match claim identity to client!")
    queue.add_to_queue(c.client_id, ["FEDeviceClaimReply", device_id, claim_result])


def fe_client_info(identity, msg):
    """
    """
    return True


def fe_ping(identity, msg):
    """
    """
    logging.debug("Firing FEPing event for %s", identity)
    event.fire(identity, "FEPing")


def fe_claim_device(identity, msg):
    """
    """
    process_id = plugin.start_claim_process(msg[1], msg[2])
    if not process_id:
        logging.warning("Claim could not start")
        return
    _claims.append(Claim(msg[2], identity, process_id))


def fe_close(identity, msg):
    """
    """
    logging.info("Shutting down socket %s", identity)
    heartbeat.remove(identity)
    remove_claim(device_process_id=identity)
    # TODO: release all devices


def fe_release_device(msg, client):
    """
    """
    pass


def fe_register_plugin(identity, msg):
    logging.info("Plugin registering socket %s as %s", identity, msg[1])
    heartbeat.start(identity)
    # If count is true, we have a count process to file off
    if msg[2] is True:
        plugin.add_count_socket(msg[1], identity)
        return
    # Otherwise, this process has been brought up for a device claim. Start a
    # device claim cycle.
    plugin.add_device_socket(msg[1], identity)
    logging.info("New claim process!")
    c = find_claim(device_process_id=identity)
    if c is None:
        raise RuntimeError("Claim for device id %s not found!" % identity)
    queue.add_to_queue(identity, ["FEDeviceClaim", msg[1], c.device_address])


def fe_register_client(identity, msg):
    logging.info("Client registering socket %s as %s", identity, msg[1])
    heartbeat.start_heartbeat(identity)
    queue.add_to_queue(identity, ["FERegisterClient"])


#PEP8ize message names
FE_CAP_RE = re.compile('^FE')
FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


def convert_msgname(name):
    s0 = FE_CAP_RE.sub(r'fe', name)
    s1 = FIRST_CAP_RE.sub(r'\1_\2', s0)
    return ALL_CAP_RE.sub(r'\1_\2', s1).lower()


def parse_message(identity, msg):
    if not isinstance(msg, (list, tuple)):
        logging.debug("NOT A LIST: %s", msg)
        return
    if len(msg) is 0:
        logging.debug("NULL LIST")
        return
    # TODO: Stop trusting the user will send a valid message name
    func_name = convert_msgname(msg[0])
    if "fe_" not in func_name:
        c = find_claim(device_address=msg[0])
        if c is not None:
            queue.add_to_queue(c.device_process_id, msg[1:])
        elif find_claim(device_process_id=identity) is not None:
            c = find_claim(device_process_id=identity)
            m = [c.device_address] + list(msg)
            queue.add_to_queue(c.client_id, m)
        else:
            raise RuntimeError("Function %s unknown or device address not found!" % msg[0])
        return None
    # if msg[0] not in ["FERegisterPlugin", "FERegisterClient"]:
    #     logging.info("Unregistered socket trying to call functions!")
    #     return None
    if func_name not in dir(sys.modules[__name__]):
        logging.info("No related function for name %s", func_name)
        return None
    # TODO: This is basically an eval. So bad. So very bad. But so very lazy. :D
    return getattr(sys.modules[__name__], func_name)(identity, msg)
