import os
import json
import argparse
import logging
from os.path import expanduser

_cdirs = {"config": os.path.join(expanduser("~"), ".fuckeverything"),
          "plugin": os.path.join(expanduser("~"), ".fuckeverything", "plugins")}

_default_server_addr = "tcp://127.0.0.1:9389"

_config = {"server_address": _default_server_addr,
           "ping_rate": 1,
           "ping_max": 3}

def _load():
    logging.debug("Loading JSON Config from %s", os.path.join(_cdirs["config"], "config.json"))
    with open(os.path.join(_cdirs["config"], "config.json"), "r+") as f:
        j = json.load(f)
        for (k, v) in j.items():
            if k in _config:
                _config[k] = v
            else:
                raise KeyError("Unexpected key %s found in configuration file!" % k)


def _save():
    logging.debug("Saving JSON Config to %s", os.path.join(_cdirs["config"], "config.json"))
    with open(os.path.join(_cdirs["config"], "config.json"), "w") as f:
        json.dump(_config, f)


def init():
    """Initialize configuration values for server"""
    parser = argparse.ArgumentParser(description="FuckEverything")
    parser.add_argument('--server_address', metavar='addr', type=str,
                        help='Address to listen on', default=_config["server_address"])
    parser.add_argument('--config_dir', metavar='path', type=str,
                        help='configuration directory', default=_cdirs["config"])
    parser.add_argument('--config_no_create_dir', action="store_true",
                        help='configuration directory')
    args = parser.parse_args()

    if args.config_dir:
        _cdirs["config"] = os.path.abspath(args.config_dir)
        _cdirs["plugin"] = os.path.join(_cdirs["config"], "plugins")
    if not os.path.exists(_cdirs["config"]):
        if args.config_no_create_dir:
            raise RuntimeError("Configuration directory does not exist!")
        logging.debug("Creating directory %s", _cdirs["config_dir"])
        os.makedirs(_cdirs["config"])
    if not os.path.exists(os.path.join(_cdirs["config"], "config.json")):
        _save()
    else:
        _load()
    if not os.path.exists(_cdirs["plugin"]):
        if args.config_no_create_dir:
            raise RuntimeError("Plugin directory does not exist!")
        logging.debug("Creating directory %s", _cdirs["plugin"])
        os.makedirs(_cdirs["plugin"])

    # only reset the server address if it's not the default
    if args.server_address != _default_server_addr:
        set_value("server_address", args.server_address)


def get_value(key):
    if key not in _config.keys():
        raise KeyError("Config value %s does not exist!" % key)
    logging.debug("Config value %s is %s", key, _config[key])
    return _config[key]


def set_value(key, value):
    if key not in _config.keys():
        raise KeyError("Config value %s does not exist!" % key)
    _config[key] = value
    logging.debug("Setting config value %s to %s", key, _config[key])
    _save()


def get_dir(key):
    if key not in _cdirs.keys():
        raise KeyError("Config dir %s does not exist!" % key)
    logging.debug("Config dir %s is %s", key, _cdirs[key])
    return _cdirs[key]
