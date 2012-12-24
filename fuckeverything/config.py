import os
import sys

CONF_DIR = os.path.join(os.path.expanduser("~"), ".fuckeverything")
PLUGIN_DIR = os.path.join(CONF_DIR, "plugins")


def init_config():
    """Initialize configuration values for server"""
    if not os.path.exists(CONF_DIR):
        os.makedirs(CONF_DIR)
    if not os.path.exists(PLUGIN_DIR):
        os.makedirs(PLUGIN_DIR)
    sys.path.append(PLUGIN_DIR)
