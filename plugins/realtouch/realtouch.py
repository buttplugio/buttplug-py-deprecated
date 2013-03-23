# librealtouch Python Module
# By qDot (Kyle Machulis)
# http://www.github.com/qdot/librealtouch
#
# Simple Proof of Concept library for direct USB control of the
# realtouch toy. Only works on linux for the time being.
#
# USB commands map to CDK commands almost directly. All commands sent
# as USB interrupt packets (read/write to hidraw currently).

import sys
import array
import hid

class RealTouchDevice(object):
    VID = 0x1f54
    PID = 0x0001

    def __init__(self):
        pass

    @staticmethod
    def getDeviceList():
        devices = []
        for d in hid.enumerate(RealTouchDevice.VID, RealTouchDevice.PID):
            devices.append(d["path"])
        return devices

    def open(self, path):
        self._device = hid.device()
        self._device.open_path(path)

    def getSerial(self):
        g = array.array('B', [0] * 64)
        g[0] = 0xa
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]

    def getFirmwareVersion(self):
        g = array.array('B', [0] * 64)
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]

    def setHeat(self, magnitude):
        g = array.array('B', [0] * 64)
        g[0] = 0x05
        g[1] = magnitude
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]
      
    def fireLube(self, magnitude, duration):
        g = array.array('B', [0] * 64)
        # Command byte 0x06
        g[0] = 0x06
        # Magnitude, single byte
        g[1] = magnitude
        # Time in milliseconds, 2 bytes, little endian packing
        g[2] = duration & 0xff
        g[3] = (duration & 0xff00) >> 0x8
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]
        
    def stopMovement(self, axis):
        # Mapping of CDK Stop command values to USB command values
        stop_dict = {
            "T" : 0x00,
            "B" : 0x10,
            "U" : 0x20,
            "S" : 0x30,
            "H" : 0x40,
            "L" : 0x50,
            "A" : 0x60
        }
        g = array.array('B', [0] * 64)
        g[0] = 0x01
        g[1] = stop_dict[axis]
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]
        
    def vectorMovement(self, magnitude, axis, direction, duration,
                       inMagnitude = 0x0, inDuration = 0x0,
                       outMagnitude = 0x0, outDuration = 0x0):
        axis_dict = {
            "T" : 0x00,
            "B" : 0x10,
            "U" : 0x20,
            "S" : 0x30
        }
        g = array.array('B', [0] * 64)
        g[0] = 0x02
        g[1] = axis_dict[axis]
        if direction == "OUT":
            g[1] += 0x80
        g[2] = magnitude
        g[3] = duration & 0xff
        g[4] = (duration & 0xff00) >> 0x8
        g[5] = inMagnitude
        g[6] = inDuration & 0xff
        g[7] = (inDuration & 0xff00) >> 0x8
        g[9] = outMagnitude
        g[9] = outDuration & 0xff
        g[10] = (outDuration & 0xff00) >> 0x8
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]

    def periodicMovement(self, period, magnitude, axis, direction,
                         duration, inMagnitude = 0x0, inDuration =
                         0x0, outMagnitude = 0x0, outDuration = 0x0):
        axis_dict = {
            "T" : 0x00,
            "B" : 0x10,
            "U" : 0x20,
            "S" : 0x30
        }
        g = array.array('B', [0] * 64)
        g[0] = 0x03
        g[1] = axis_dict[axis]
        if direction == "OUT":
            g[1] += 0x80
        g[2] = magnitude
        g[3] = duration & 0xff
        g[4] = (duration & 0xff00) >> 0x8
        g[5] = period
        g[6] = inMagnitude
        g[7] = inDuration & 0xff
        g[8] = (inDuration & 0xff00) >> 0x8
        g[9] = outMagnitude
        g[10] = outDuration & 0xff
        g[11] = (outDuration & 0xff00) >> 0x8
        self._device.write(g)
        print ["0x%.02x " % (ord(x)) for x in self._device.read(64)]

def main():
    r = RealTouchDevice()
    
    r.getSerial()
    r.getFirmwareVersion()
    r.vectorMovement(255, "U", "OUT", 1000)
    return 0

if __name__ == "__main__":
    sys.exit(main())
