from fuckeverything import device
from fuckeverything import plugin
from fuckeverything import feinfo
from fuckeverything import queue
from fuckeverything import heartbeat
import re
import sys


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
    plugin.update_device_list(identity, msg[1])


def fe_device_claim(identity, msg):
    """
    """
    pass


def fe_client_info(identity, msg):
    """
    """
    return True


def fe_ping(identity, msg):
    """
    """
    heartbeat.update(identity)


def fe_claim_device(msg):
    """
    """
    device_id = msg[0]
    if not device.add_device_claim(device_id, client):
        return False
    return True


def fe_close(identity, msg):
    """
    """
    print "Shutting down socket %s" % (identity)
    heartbeat.remove(identity)
    # TODO: release all devices


def fe_release_device(msg, client):
    """
    """
    pass


def fe_register_plugin(identity, msg):
    print "Plugin registering socket %s as %s" % (identity, msg[1])
    heartbeat.add(identity)
    if msg[2] is True:
        plugin.add_count_socket(msg[1], identity)


def fe_register_client(identity, msg):
    print "Client registering socket %s as %s" % (identity, msg[1])
    heartbeat.add(identity)
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
        print "NOT A LIST: %s" % (msg)
        return
    if len(msg) is 0:
        print "NULL LIST"
        return
    # TODO: Stop trusting the user will send a value message name
    func_name = convert_msgname(msg[0])
    if not heartbeat.contains(identity) and msg[0] not in ["FERegisterPlugin", "FERegisterClient"]:
        print "Unregistered socket trying to call functions!"
        return
    if func_name not in dir(sys.modules[__name__]):
        print "No related function for name %s" % func_name
        return None
    # This is basically an eval. So bad. So very bad. But so very lazy. :D
    return getattr(sys.modules[__name__], func_name)(identity, msg)
