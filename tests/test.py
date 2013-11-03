import sys
import os
import unittest
import shutil
import mock
import json
import tempfile
import time
import msgpack
import logging
import gevent
import zmq.green as zmq
from buttplug.core import config
from buttplug.core import plugin
from buttplug.core import utils
from buttplug.core import queue
from buttplug.core import system
from buttplug.core import event
from buttplug.core import server
from buttplug.template.client import BPClient

_test_plugin_json = {"name": "Test Plugin",
                     "version": "0.001",
                     "executable": "test-plugin",
                     "messages": ["RawTestMsg", "BPDeviceCount"]}

def _copy_test_plugin(base_dir):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    with open(os.path.join(base_dir, plugin.Plugin.PLUGIN_INFO_FILE), "w") as f:
        json.dump(_test_plugin_json, f)
    shutil.copy(os.path.join(os.getcwd(), "scripts", "test-plugin"), base_dir)
    shutil.copytree(os.path.join(os.getcwd(), "buttplug"), os.path.join(base_dir, "buttplug"))


class TestClient(BPClient):

    def __init__(self, port):
        super(TestClient, self).__init__()
        self.server_port = port

    # Override command line parsing since we don't have one
    def setup_parser(self):
        return True

    # Override command line parsing since we don't have one
    def parse_arguments(self):
        return True


class ConfigTests(unittest.TestCase):

    def setUp(self):
        reload(config)
        reload(utils)
        self.tmpdir = tempfile.mkdtemp(prefix="fetest-")
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            config.init()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def testHelp(self):
        """help test, should just bail out."""
        reload(config)
        with mock.patch('sys.argv', ['buttplug', '-h']):
            try:
                config.init()
                self.fail("Not throwing exception to quit program after help list!")
            except SystemExit:
                pass

    def testDirectoryCreation(self):
        """create a new config directory and populate it"""
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            config.init()
        self.failIf(not os.path.exists(config._cdirs["config"]))
        self.failIf(not os.path.exists(config._cdirs["plugin"]))

    def testDirectoryNoCreation(self):
        """do not create new directory if it doesn't exist, fail out instead"""
        reload(config)
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir + "abc", "--config_no_create_dir"]):
            try:
                config.init()
                self.fail("Not throwing exception on missing configuration directories!")
            except RuntimeError:
                pass

    def testInvalidConfigValue(self):
        """throw when we get a bad config value"""
        try:
            config.get_value("testing")
            self.fail("Not throwing expection on missing configuration option!")
        except KeyError:
            pass

    def testValidConfigValue(self):
        """get a matching config value"""
        v = config.get_value("server_address")
        self.failIf(v != config._config["server_address"])

    def testConfigFileCreation(self):
        """create config files correctly"""
        self.failIf(not os.path.exists(os.path.join(config._cdirs["config"], config.CONFIG_FILENAME)))

    def testConfigFileLoad(self):
        """load config files correctly"""
        config.set_value("server_address", "ipc://wat")
        reload(config)
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            config.init()
            self.failIf(config.get_value("server_address") != "ipc://wat")

    def testInvalidConfigurationFileLoad(self):
        """throw on screwed config files correctly"""
        config.set_value("server_address", "ipc://wat")
        # Insert gibberish!
        with open(os.path.join(config._cdirs["config"], config.CONFIG_FILENAME), "w") as f:
            f.write("This is so not some fucking json")
        reload(config)
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            try:
                config.init()
                self.fail("Didn't fail on gibberish json!")
            except ValueError:
                pass

    def testInvalidConfigurationKeyLoad(self):
        """throw on screwed config files correctly"""
        config.set_value("server_address", "ipc://wat")
        # Insert bad key!
        with open(os.path.join(config._cdirs["config"], config.CONFIG_FILENAME), "w") as f:
            json.dump({"server_addres": "tcp://127.0.0.1:9389"}, f)
        reload(config)
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            try:
                config.init()
                self.fail("Didn't fail on gibberish json!")
            except KeyError:
                pass


class PluginTests(unittest.TestCase):
    def setUp(self):
        reload(config)
        reload(plugin)
        reload(server)
        reload(utils)
        self.tmpdir = tempfile.mkdtemp(prefix="fetest-")
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            config.init()
        self.plugin_dest = os.path.join(config.get_dir("plugin"), "test-plugin")
        self.server_loop_trigger = gevent.event.Event()

        def server_loop():
            server.init()
            utils.spawn_gevent_func("main socket loop", "main", server.msg_loop)
            gevent.sleep()
            self.server_loop_trigger.wait()
            server.shutdown()
        self.server_greenlet = gevent.spawn(server_loop)

    def copyPlugin(self):
        # Copy plugin to directory here
        _copy_test_plugin(self.plugin_dest)

    def tearDown(self):
        self.server_loop_trigger.set()
        self.server_greenlet.join()
        shutil.rmtree(self.tmpdir)

    def testNoPlugins(self):
        """have no plugins"""
        plugin.scan_for_plugins()
        # If we've actually started any greenlets, fail
        self.failIf("plugin" in utils._pools.keys())

    def testOnePluginCorrectJSON(self):
        """have valid plugin, with a valid count process"""
        self.copyPlugin()
        plugin.scan_for_plugins()
        gevent.sleep(.3)
        self.failIf(len(plugin.plugins_available()) != 1)

    def testOnePluginIncorrectJSON(self):
        """have plugin with invalid json"""
        # Copy plugin to directory here
        self.copyPlugin()
        # Edit json
        with open(os.path.join(self.plugin_dest, plugin.Plugin.PLUGIN_INFO_FILE), "w") as f:
            f.write("This is so not some fucking json")
        plugin.scan_for_plugins()
        gevent.sleep(.3)
        self.failIf(len(plugin.plugins_available()) > 0)

    def testInvalidCountProcess(self):
        """have plugin whose count process doesn't come up"""
        self.copyPlugin()
        # Fuck with the plugin executable script
        with open(os.path.join(self.plugin_dest, "test-plugin"), "w") as f:
            f.write("This is so not executable")
        plugin.scan_for_plugins()
        gevent.sleep(.3)
        self.failIf(len(plugin.plugins_available()) > 0)


class HeartbeatTests(unittest.TestCase):

    class HeartbeatTestSocket(TestClient):
        def __init__(self, port, evt):
            super(HeartbeatTests.HeartbeatTestSocket, self).__init__(port)
            self.ping_count = 0
            self.evt = evt

        # Override ping reply of base class
        def ping_reply(self, msg):
            self.last_ping = time.time()
            self.send(["s", "BPPing"])
            self.ping_count = self.ping_count + 1
            if self.ping_count == 3:
                self.evt.set()

        def close(self, msg):
            TestClient.close(self, msg)
            self.evt.set()

    def setUp(self):
        reload(config)
        reload(server)
        reload(utils)
        self.tmpdir = tempfile.mkdtemp(prefix="fetest-")
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            config.init()
        # Set ping rates REALLY low so these will move quickly
        config.set_value("ping_rate", .01)
        config.set_value("ping_max", .05)
        self.trigger = gevent.event.Event()
        self.server_loop_trigger = gevent.event.Event()

        def server_loop():
            server.init()
            utils.spawn_gevent_func("main socket loop", "main", server.msg_loop)
            gevent.sleep()
            self.server_loop_trigger.wait()
            server.shutdown()

        self.server_greenlet = gevent.spawn(server_loop)

        # Start a new socket
        self.test_socket = HeartbeatTests.HeartbeatTestSocket(config.get_value("server_address"), self.trigger)
        # Attach to router
        self.test_socket_greenlet = gevent.spawn(self.test_socket.run)

    def tearDown(self):
        self.test_socket.close(None)
        self.server_loop_trigger.set()
        self.server_greenlet.join()
        shutil.rmtree(self.tmpdir)

    def testSucceedHeartbeat(self):
        """Tests heartbeat normal success"""
        # Crank for a few
        self.failIf(not self.trigger.wait(timeout=1), "Did not ping before timeout!")

    def testFailHeartbeat(self):
        """Tests heartbeat failure"""
        def no_ping(msg):
            pass
        self.test_socket.inmsg["BPPing"] = no_ping
        self.failIf(self.trigger.wait(timeout=.5), "Did not close before timeout!")

    def testRemoveHeartbeat(self):
        """Tests heartbeat removal list"""
        def sleeplet():
            try:
                gevent.sleep(1000)
            except utils.BPGreenletExit:
                pass
        hb = utils.spawn_heartbeat("Does not matter", self.test_socket_greenlet)
        hb.join(timeout=.5)
        self.failIf(not hb.successful(), "Heartbeat did not exit!")


class EventTests(unittest.TestCase):

    def setUp(self):
        reload(event)

    def testSuccessfulEvent(self):
        """Test queuing an event, then having it fire"""
        e = event.add("testing", "testing")
        event.fire("testing", ["testing", "testing"])
        self.failIf(not e.successful(), "Event did not fire!")

    def testMultipleEventTriggers(self):
        """Test getting multiple replies for the same event"""
        e = event.add("testing", "testing")
        event.fire("testing", ["testing", "testing"])
        event.fire("testing", ["testing", "testing"])
        self.failIf(not e.successful(), "Event did not fire!")


class ClaimFlowTests(unittest.TestCase):
    class ClaimFlowTestSocket(TestClient):
        def __init__(self, port):
            super(ClaimFlowTests.ClaimFlowTestSocket, self).__init__(port)

        def get_device_list(self):
            self.send(["s", "BPDeviceList"])

    def copyPlugin(self):
        # Copy plugin to directory here
        _copy_test_plugin(self.plugin_dest)

    def setUp(self):
        reload(config)
        reload(plugin)
        reload(server)
        reload(utils)
        self.tmpdir = tempfile.mkdtemp(prefix="fetest-")
        with mock.patch('sys.argv', ['buttplug', '--config_dir', self.tmpdir]):
            config.init()
        self.plugin_dest = os.path.join(config.get_dir("plugin"), "test-plugin")
        self.server_loop_trigger = gevent.event.Event()
        self.copyPlugin()
        plugin.scan_for_plugins()

        def server_loop():
            server.init()
            utils.spawn_gevent_func("main socket loop", "main", server.msg_loop)
            gevent.sleep()
            self.server_loop_trigger.wait()
            server.shutdown()
        self.server_greenlet = gevent.spawn(server_loop)

        # Start a new socket
        self.test_socket = ClaimFlowTests.ClaimFlowTestSocket(config.get_value("server_address"))
        # Attach to router
        self.test_socket_greenlet = gevent.spawn(self.test_socket.run)

    def tearDown(self):
        self.server_loop_trigger.set()
        self.server_greenlet.join()
        shutil.rmtree(self.tmpdir)

    def testClientDeviceListFetch(self):
        """Connect client, fetch device list"""
        # TODO: Figure out a better way to make sure we have a plugin ready to go
        gevent.sleep(.1)
        e = gevent.event.AsyncResult()
        def device_list(msg):
            e.set(msg)
        self.test_socket.inmsg["BPDeviceList"] = device_list
        self.test_socket.get_device_list()
        list_msg = None
        try:
            list_msg = e.get(block=True, timeout=1)
        except gevent.Timeout:
            self.fail("Timed out waiting for device list!")

        self.failIf(list_msg is None)
        self.failIf(list_msg[1] != "BPDeviceList")
        print list_msg
        self.failIf("TestSuccessfulOpen" not in list_msg[2][0]["devices"])
#     # def testClaimValidDevice(self):
#     #     """Claim a device"""
#     #     self.test_socket.send(["s", "BPClaimDevice", ""])
#     #     # We're in the ctd and dtc dicts
#     #     # We've got a heartbeat

#     #     pass

    # def testDroppedClientSocket(self):
    #     """Start claiming a device, drop client socket before plugin bringup"""
    #     pass

    # def testDroppedPluginSocket(self):
    #     """Start claiming a device to point of plugin bringup, drop plugin socket"""
    #     pass

    # def testClaimInvalidDevice(self):
    #     """Claim a device whose bus address does not exist"""
    #     pass

    # def testClientPingTimeoutOnClaim(self):
    #     """Start claim, let client ping timeout"""
    #     pass

    # def testPluginPingTimeoutOnClaim(self):
    #     """Start claim, let plugin ping timeout"""
    #     pass

    # def testMultipleClaimRequests(self):
    #     """Test requesting the same claim multiple times from the same client"""
    #     pass

    # def testClaimRace(self):
    #     """Test requesting the same claim at the same time from different clients"""
    #     pass

    # def testAlreadyClaimedDevice(self):
    #     """Claim a device, then try to claim it again after successfully claiming it"""
    #     pass


# # class ProcessTests(unittest.TestCase):
# #     pass


# # class ServerTests(unittest.TestCase):
# #     pass


# # class UtilsTests(unittest.TestCase):
# #     pass
