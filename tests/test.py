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
sys.path.append("/home/qdot/code/git-projects/fuckeverything")
from fuckeverything.core import config
from fuckeverything.core import plugin
from fuckeverything.core import process
from fuckeverything.core import utils
from fuckeverything.core import heartbeat
from fuckeverything.core import queue
from fuckeverything.core import system
from fuckeverything.core import server


class TestSocket(object):
    def __init__(self, port):
        self.context = zmq.Context()
        self.identity = utils.random_ident()
        self.socket_queue = self.context.socket(zmq.PUSH)
        self.socket_queue.bind("inproc://fe-%s" % (self.identity))
        self.socket_out = self.context.socket(zmq.PULL)
        self.socket_out.connect("inproc://fe-%s" % (self.identity))
        self.socket_client = self.context.socket(zmq.DEALER)
        self.socket_client.setsockopt(zmq.IDENTITY, self.identity)
        self.socket_client.connect(port)

    def send(self, msg):
        self.socket_queue.send(msgpack.packb(msg))

    def parse_message(self, msg):
        raise RuntimeError("Needs to be defined by test!")

    def run(self):
        while True:
            poller = zmq.Poller()
            poller.register(self.socket_client, zmq.POLLIN)
            poller.register(self.socket_out, zmq.POLLIN)

            socks = dict(poller.poll(10))
            if self.socket_client in socks and socks[self.socket_client] == zmq.POLLIN:
                msg = self.socket_client.recv()
                self.parse_message(msgpack.unpackb(msg))

            if self.socket_out in socks and socks[self.socket_out] == zmq.POLLIN:
                msg = self.socket_out.recv()
                self.socket_client.send(msg)

    def close(self):
        self.socket_client.close()
        self.socket_queue.close()
        self.socket_out.close()


class ConfigTests(unittest.TestCase):

    def setUp(self):
        reload(config)
        self.tmpdir = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def testHelp(self):
        """help test, should just bail out."""
        reload(config)
        with mock.patch('sys.argv', ['fuckeverything', '-h']):
            try:
                config.init()
                self.fail("Not throwing exception to quit program after help list!")
            except SystemExit:
                pass

    def testDirectoryCreation(self):
        """create a new config directory and populate it"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        self.failIf(not os.path.exists(config._cdirs["config"]))
        self.failIf(not os.path.exists(config._cdirs["plugin"]))

    def testDirectoryNoCreation(self):
        """do not create new directory if it doesn't exist, fail out instead"""
        reload(config)
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir + "abc", "--config_no_create_dir"]):
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
        self.failIf(not os.path.exists(os.path.join(config._cdirs["config"], "config.json")))

    def testConfigFileLoad(self):
        """load config files correctly"""
        config.set_value("server_address", "ipc://wat")
        reload(config)
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
            self.failIf(config.get_value("server_address") != "ipc://wat")

    def testInvalidConfigurationFileLoad(self):
        """throw on screwed config files correctly"""
        config.set_value("server_address", "ipc://wat")
        # Insert gibberish!
        with open(os.path.join(config._cdirs["config"], "config.json"), "w") as f:
            f.write("This is so not some fucking json")
        reload(config)
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            try:
                config.init()
                self.fail("Didn't fail on gibberish json!")
            except ValueError:
                pass

    def testInvalidConfigurationKeyLoad(self):
        """throw on screwed config files correctly"""
        config.set_value("server_address", "ipc://wat")
        # Insert bad key!
        with open(os.path.join(config._cdirs["config"], "config.json"), "w") as f:
            json.dump({"server_addres": "tcp://127.0.0.1:9389"}, f)
        reload(config)
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            try:
                config.init()
                self.fail("Didn't fail on gibberish json!")
            except KeyError:
                pass


class PluginTests(unittest.TestCase):
    def setUp(self):
        reload(config)
        reload(plugin)
        self.tmpdir = tempfile.mkdtemp()
        self.plugin_dest = ""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()

    def copyPlugin(self):
        # Copy plugin to directory here
        plugin_path = os.path.join(os.getcwd(), "tests", "example-plugin")
        self.plugin_dest = os.path.join(config.get_dir("plugin"), "example")
        shutil.copytree(plugin_path, self.plugin_dest)

    def tearDown(self):
        process.kill_all(False)
        shutil.rmtree(self.tmpdir)
        pass

    def testNoPlugins(self):
        """have no plugins"""
        plugin.scan_for_plugins()
        self.failIf(len(plugin.plugins_available()) > 0)

    def testOnePluginCorrectJSON(self):
        """have valid plugin"""
        self.copyPlugin()
        plugin.scan_for_plugins()
        self.failIf(len(plugin.plugins_available()) == 0)

    def testOnePluginIncorrectJSON(self):
        """have plugin with invalid json"""
        # Copy plugin to directory here
        self.copyPlugin()
        # Edit json
        with open(os.path.join(self.plugin_dest, "feplugin.json"), "w") as f:
            f.write("This is so not some fucking json")
        plugin.scan_for_plugins()
        self.failIf(len(plugin.plugins_available()) > 0)

    def testValidCountProcess(self):
        """have plugin with live count process"""
        self.copyPlugin()
        plugin.scan_for_plugins()
        plugin.start_plugin_counts()
        # Put a sleep in, so that the count process can actually come up
        # TODO: Make this a registration test instead of a sleep
        time.sleep(.1)
        # If plugin count process doesn't come up, it's removed from list
        self.failIf(len(plugin.plugins_available()) == 0)

    def testInvalidCountProcess(self):
        """have plugin whose count process doesn't come up"""
        self.copyPlugin()
        plugin.scan_for_plugins()
        # Fuck with the plugin executable script
        with open(os.path.join(self.plugin_dest, "scripts", "plugin.py"), "w") as f:
            f.write("This is so not executable")
        plugin.start_plugin_counts()
        self.failIf(len(plugin.plugins_available()) > 0)


class HeartbeatTests(unittest.TestCase):

    class HeartbeatTestSocket(TestSocket):
        def __init__(self, port, evt):
            super(HeartbeatTests.HeartbeatTestSocket, self).__init__(port)
            self.ping_count = 0
            self.evt = evt

        def parse_message(self, msg):
            msg_dest = msg[0]
            msg_type = msg[1]
            if msg_type == "FEPing":
                self.send(["s", "FEPing"])
                self.ping_count = self.ping_count + 1
                if self.ping_count == 3:
                    self.evt.set()

    def setUp(self):
        reload(config)
        reload(server)
        reload(heartbeat)
        self.tmpdir = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        # Set ping rates REALLY low so these will move quickly
        config.set_value("ping_rate", .01)
        config.set_value("ping_max", .05)
        server.init()
        self.e = gevent.event.Event()
        # Start a new socket
        self.s = HeartbeatTests.HeartbeatTestSocket(config.get_value("server_address"), self.e)
        # sorten ping rates so things don't take forever
        # Attach to router
        self.r = gevent.spawn(self.s.run)

        def server_loop():
            while True:
                server.msg_loop()
        self.t = gevent.spawn(server_loop)
        # Add to heartbeat
        self.g = heartbeat.start(self.s.identity)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        self.s.close()
        server.shutdown()

    def testSucceedHeartbeat(self):
        """Tests heartbeat normal success"""
        # Crank for a few
        self.e.wait(.1)
        self.r.kill()
        self.t.kill()
        # Make sure we're still actually running our heartbeat
        self.failIf(self.g.successful())

    def testFailHeartbeat(self):
        """Tests heartbeat failure"""
        # Attach to router
        self.e.wait(.1)
        # kill our own message loop, let the server message loop run
        self.r.kill()
        gevent.sleep(.1)
        self.t.kill()
        # Heartbeat should've died by now
        self.failIf(not self.g.successful())

    def testRemoveHeartbeat(self):
        """Tests heartbeat removal list"""
        self.e.wait(.1)
        # kill our own message loop, let the server message loop run
        self.r.kill()
        heartbeat.remove(self.s.identity)
        gevent.sleep(.01)
        self.t.kill()
        # We should've died AND removal list should be clear
        self.failIf(not self.g.successful() and len(heartbeat._removal) == 0)


class ClaimFlowTests(unittest.TestCase):

    def testDroppedSocket(self):
        pass

    def testClaimDisappearedDevice(self):
        pass

    def testClaimValidDevice(self):
        pass

    def testClaimDuringClientDeath(self):
        pass

    def testClaimOnClientShutdown(self):
        pass

    def testClaimOnPluginShutdown(self):
        pass


class ProcessTests(unittest.TestCase):
    pass


class ClientTests(unittest.TestCase):
    pass


class EventTests(unittest.TestCase):
    pass


class QueueTests(unittest.TestCase):
    pass


class ServerTests(unittest.TestCase):
    pass


class UtilsTests(unittest.TestCase):
    pass
