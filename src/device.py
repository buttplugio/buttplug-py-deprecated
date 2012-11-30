import plugin

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
        devs[k]["claims"] = []
        _mvars["id"] += 1
    return devs

def devicesAvailable():
    """
    """
    return _mvars["devices"]

def addDeviceClaim(device_id, client_id):
    print "Adding claim"
    device = None
    for (k,v) in _mvars["devices"].items():
        if v["id"] == device_id:
            device = v
            break
    # First off, is it already claimed?
    if len(device["claims"]) > 0 and not device["plugin"].MULTICLAIM:
        print "Device already claimed"
        return False
    device["claims"].append(client_id)
    # We're the first to claim, so open it
    if len(device["claims"]) == 1:
        device["device"] = device["plugin"].getDevice(device["device_info"])
        if device["device"] == None:
            print "Can't open device"
            return False    
    print "Device claimed"
    return True

def removeDeviceClaim(device_id, client_id):
    devs = _mvars["devices"]
        
