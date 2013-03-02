import os
import sys
import argparse

CONF_DIR = os.path.join("/home/qdot/.fuckeverything")
PLUGIN_DIR = os.path.join(CONF_DIR, "plugins")
# SERVER_ADDRESS = "ipc://fetest"
SERVER_ADDRESS = "tcp://127.0.0.1:9389"
PING_RATE = 1
PING_MAX = 3

def init_arguments():
    

def init_config():
    """Initialize configuration values for server"""
    if not os.path.exists(CONF_DIR):
        raise RuntimeError("Configuration directory does not exist!")
    if not os.path.exists(PLUGIN_DIR):
        raise RuntimeError("Plugin directory does not exist!")
