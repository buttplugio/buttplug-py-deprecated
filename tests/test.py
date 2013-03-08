import sys
import os
import unittest
import shutil
import mock
import json
import tempfile
import time
sys.path.append("/home/qdot/code/git-projects/fuckeverything")
from fuckeverything import config
from fuckeverything import plugin
from fuckeverything import process
# from fuckeverything import queue
# from fuckeverything import system
# from fuckeverything import heartbeat

class ConfigTests(unittest.TestCase):

    def setUp(self):
        reload(config)
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def testHelp(self):
        """help test, should just bail out."""
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
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir, "--config_no_create_dir"]):
            try:
                config.init()
                self.fail("Not throwing exception on missing configuration directories!")
            except RuntimeError:
                pass

    def testInvalidConfigValue(self):
        """throw when we get a bad config value"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        try:
            config.get_value("testing")
            self.fail("Not throwing expection on missing configuration option!")
        except KeyError:
            pass

    def testValidConfigValue(self):
        """get a matching config value"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        v = config.get_value("server_address")
        self.failIf(v != config._config["server_address"])

    def testConfigFileCreation(self):
        """create config files correctly"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        self.failIf(not os.path.exists(os.path.join(config._cdirs["config"], "config.json")))

    def testConfigFileLoad(self):
        """load config files correctly"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
            config.set_value("server_address", "ipc://wat")
            reload(config)
            config.init()
            self.failIf(config.get_value("server_address") != "ipc://wat")

    def testInvalidConfigurationFileLoad(self):
        """throw on screwed config files correctly"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
            config.set_value("server_address", "ipc://wat")
            # Insert gibberish!
            with open(os.path.join(config._cdirs["config"], "config.json"), "w") as f:
                f.write("This is so not some fucking json")
            reload(config)
            try:
                config.init()
                self.fail("Didn't fail on gibberish json!")
            except ValueError:
                pass

    def testInvalidConfigurationKeyLoad(self):
        """throw on screwed config files correctly"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
            config.set_value("server_address", "ipc://wat")
            # Insert bad key!
            with open(os.path.join(config._cdirs["config"], "config.json"), "w") as f:
                json.dump({"server_addres": "tcp://127.0.0.1:9389"}, f)
            reload(config)
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
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        plugin.scan_for_plugins()
        self.failIf(len(plugin.plugins_available()) > 0)

    def testOnePluginCorrectJSON(self):
        """have valid plugin"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        self.copyPlugin()
        plugin.scan_for_plugins()
        self.failIf(len(plugin.plugins_available()) == 0)

    def testOnePluginIncorrectJSON(self):
        """have plugin with invalid json"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        # Copy plugin to directory here
        self.copyPlugin()
        # Edit json
        with open(os.path.join(self.plugin_dest, "feplugin.json"), "w") as f:
            f.write("This is so not some fucking json")
        plugin.scan_for_plugins()
        self.failIf(len(plugin.plugins_available()) > 0)

    def testValidCountProcess(self):
        """have plugin with live count process"""
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
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
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', self.tmpdir]):
            config.init()
        self.copyPlugin()
        plugin.scan_for_plugins()
        # Fuck with the plugin executable script
        with open(os.path.join(self.plugin_dest, "scripts", "plugin.py"), "w") as f:
            f.write("This is so not executable")
        plugin.start_plugin_counts()
        self.failIf(len(plugin.plugins_available()) > 0)


class HeartbeatTests(unittest.TestCase):

    def testAddHeartbeat(self):
        pass

    def testRemoveHeartbeat(self):
        pass

    def testSucceedHeartbeat(self):
        pass

    def testFailHeartbeat(self):
        pass


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
