import sys
import os
import unittest
import shutil
import mock
sys.path.append("/home/qdot/code/git-projects/fuckeverything")
from fuckeverything import config
# from fuckeverything import plugin
# from fuckeverything import queue
# from fuckeverything import system
# from fuckeverything import heartbeat

# argparse sys.argv testing using mock
# via http://www.reddit.com/r/Python/comments/r9o2i/using_nose_and_argparse/
# import mock
# with mock.patch('sys.argv', ['whatever', 'I', 'wanna', 'test']):
#         pass   # do whatever you want


class ConfigTests(unittest.TestCase):

    def setUp(self):
        reload(config)

    def testHelp(self):
        """Help test. Should just bail out."""
        with mock.patch('sys.argv', ['fuckeverything', '-h']):
            try:
                config.init_config()
                self.fail("Not throwing exception to quit program after help list!")
            except SystemExit:
                pass

    def testDirectoryCreation(self):
        """Create a new config directory and populate it"""
        import tempfile
        d = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', d]):
            config.init_config()
            self.failIf(not os.path.exists(d))
            self.failIf(not os.path.exists(config._cdirs["config"]))
            self.failIf(not os.path.exists(config._cdirs["plugin"]))
        shutil.rmtree(d)

    def testDirectoryNoCreation(self):
        """Do not create new directory if it doesn't exist, fail out instead"""
        import tempfile
        d = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', d, "--config_no_create_dir"]):
            try:
                config.init_config()
                self.fail("Not throwing exception on missing configuration directories!")
            except RuntimeError:
                pass
        shutil.rmtree(d)

    def testInvalidConfigValue(self):
        """Test that we throw when we get a bad config value"""
        import tempfile
        d = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', d]):
            config.init_config()
            try:
                config.get_config_value("testing")
                self.fail("Not throwing expection on missing configuration option!")
            except KeyError:
                pass
        shutil.rmtree(d)

    def testValidConfigValue(self):
        """Test that we get a matching config value"""
        import tempfile
        d = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', d]):
            config.init_config()
            v = config.get_config_value("server_address")
            self.failIf(v != config._config["server_address"])
        shutil.rmtree(d)

    def testConfigFileCreation(self):
        """Test that we create config files correctly"""
        import tempfile
        d = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', d]):
            config.init_config()
            self.failIf(not os.path.exists(os.path.join(config._cdirs["config"], "config.json")))
        shutil.rmtree(d)

    def testConfigFileLoad(self):
        """Test that we load config files correctly"""
        import tempfile
        d = tempfile.mkdtemp()
        with mock.patch('sys.argv', ['fuckeverything', '--config_dir', d]):
            config.init_config()
            config.set_config_value("server_address", "ipc://wat")
            reload(config)
            config.init_config()
            self.failIf(config.get_config_value("server_address") != "ipc://wat")
        shutil.rmtree(d)

    def testInvalidConfigurationFileLoad(self):
        pass

