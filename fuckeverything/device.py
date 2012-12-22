from fuckeverything import plugin
from fuckeverything import client

_mvars = {"devices": {}, "id": 0}


def scan_for_devices():
    """Iterate through all plugins, making a set of all devices available to
    use."""
    new_devices = {}
    devs = _mvars["devices"]
    [new_devices.update(dict((hash(frozenset(dev.values())), {"device_info": dev, "plugin": p})
                             for dev in p.getDeviceList()))
     for p in plugin.plugins_available()]
    # Remove devices no longer connected
    dead_keys = devs.viewkeys() - new_devices.viewkeys()
    new_keys = new_devices.viewkeys() - devs.viewkeys()
    # Add new devices
    for k in dead_keys:
        del devs[k]
    for k in new_keys:
        devs[k] = new_devices[k]
        devs[k]["id"] = _mvars["id"]
        devs[k]["claims"] = {}
        _mvars["id"] += 1
    return devs


def devices_available():
    """
    Return the current list of all devices available
    """
    return _mvars["devices"]


def add_device_claim(device_id, client_inst):
    """
    See if a client can claim a certain device ID
    """
    # print "Adding claim"
    device = None
    for val in _mvars["devices"].values():
        if val["id"] == device_id:
            device = val
            break
    # First off, is it already claimed?
    if len(device["claims"]) > 0 and not device["plugin"].plugin_info["multiclaim"]:
        print "Device already claimed"
        return False
    # We're the first to claim, so open it
    if len(device["claims"]) == 0:
        device["device"] = device["plugin"].openDevice(device["device_info"])
        if not device["device"]:
            print "Can't open device"
            return False
        device["plugin"].startLoop(device)
    device["claims"][client_inst.id] = client_inst
    client_inst.devices[device_id] = device
    # print "Device claimed"
    return True


def remove_device_claim(device, client_inst):
    """
    Drop a device claim for a specific client
    """
    del device["claims"][client_inst.id]
    if len(device["claims"]) == 0:
        device["plugin"].closeDevice(device["device"])


def distribute_message(device, msg):
    """
    Distribute a message from a device to all claims
    """
    for claim in device["claims"].values():
        client.sendMessage(claim, msg)
