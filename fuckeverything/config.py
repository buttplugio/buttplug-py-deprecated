import os
import sys

CONF_DIR = os.path.join(os.path.expanduser("~"), ".fuckeverything")
PLUGIN_DIR = os.path.join(CONF_DIR, "plugins")
# SERVER_ADDRESS = "ipc://fetest"
SERVER_ADDRESS = "tcp://127.0.0.1:9389"
PING_RATE = 1
PING_MAX = 3


def init_config():
    """Initialize configuration values for server"""
    if not os.path.exists(CONF_DIR):
        os.makedirs(CONF_DIR)
    if not os.path.exists(PLUGIN_DIR):
        os.makedirs(PLUGIN_DIR)
