import plugin
import client

_mvars = { "devices" : {}, "id" : 0}

def scanForDevices():
    new_devices = {}
    devs = _mvars["devices"]
    [new_devices.update(dict((hash(frozenset(dev.values())), {"device_info": dev, "plugin": p}) for dev in p.getDeviceList())) for p in plugin.pluginsAvailable()]
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

def devicesAvailable():
    """
    """
    return _mvars["devices"]

def addDeviceClaim(device_id, client):
    # print "Adding claim"
    device = None
    for (k,v) in _mvars["devices"].items():
        if v["id"] == device_id:
            device = v
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
    device["claims"][client.id] = client
    client.devices[device_id] = device
    # print "Device claimed"
    return True

def removeDeviceClaim(device, client):
    del device["claims"][client.id]
    if len(device["claims"]) == 0:
        device["plugin"].closeDevice(device["device"])

def distributeMessage(device, msg):
    for (cid,c) in device["claims"].items():
        client.sendMessage(c, msg)
