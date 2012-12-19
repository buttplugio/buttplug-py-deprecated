import os
import sys

conf_dir = os.path.join(os.path.expanduser("~"), ".fuckeverything")
plugin_dir = os.path.join(os.path.expanduser("~"), ".fuckeverything", "plugins")

def initConfig():
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
    sys.path.append(plugin_dir)
