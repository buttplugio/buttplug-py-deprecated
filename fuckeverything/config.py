import os
import sys
import argparse
from os.path import expanduser

CONF_DIR = os.path.join(expanduser("~"), ".fuckeverything")
PLUGIN_DIR = os.path.join(CONF_DIR, "plugins")
# SERVER_ADDRESS = "ipc://fetest"
SERVER_ADDRESS = "tcp://127.0.0.1:9389"
PING_RATE = 1
PING_MAX = 3


def parse_args():
    parser = argparse.ArgumentParser(description="FuckEverything")
    parser.add_argument('--server_address', metavar='p', type=str,
                        help='Address to listen on', default="tcp://127.0.0.1:9389")
    args = parser.parse_args()

    if args.server_address:
        server_port = args.server_address
    return True


def init_config():
    """Initialize configuration values for server"""
    parse_args()
    if not os.path.exists(CONF_DIR):
        raise RuntimeError("Configuration directory does not exist!")
    if not os.path.exists(PLUGIN_DIR):
        raise RuntimeError("Plugin directory does not exist!")

