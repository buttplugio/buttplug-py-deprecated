import sys
import unittest
sys.path.append("/home/qdot/code/git-projects/fuckeverything")
from fuckeverything import config
# from fuckeverything import plugin
# from fuckeverything import queue
# from fuckeverything import system
# from fuckeverything import heartbeat


class ConfigTests(unittest.TestCase):

    def setUp(self):
        reload(config)

    def testServer(self):
        config.SERVER_ADDRESS = 'a'
        self.failIf(config.SERVER_ADDRESS != 'a')
