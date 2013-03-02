import sys
import unittest
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
        with mock.patch('sys.argv', ['-h']):
            config.init_config()

    def testDirectoryCreation(self):
        pass

    def testInvalidConfiguration(self):
        pass


