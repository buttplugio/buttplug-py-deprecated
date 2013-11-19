import os
import json
import argparse
import logging
from os.path import expanduser

_cdirs = {"config": os.path.join(expanduser("~"), ".buttplug"),
          "plugin": os.path.join(expanduser("~"), ".buttplug", "plugins")}

_default_server_addr = "tcp://127.0.0.1:9389"
_default_wsserver_addr = ""

_config = {"server_address": _default_server_addr,
           "ping_rate": 1,
           "websocket_address": _default_wsserver_addr,
           "ping_max": 3}

CONFIG_FILENAME = "config.json"


def _load():
    logging.debug("Loading JSON Config from %s", os.path.join(_cdirs["config"],
                                                              CONFIG_FILENAME))
    with open(os.path.join(_cdirs["config"], CONFIG_FILENAME), "r+") as f:
        j = json.load(f)
        for (k, v) in j.items():
            if k in _config:
                _config[k] = v
            else:
                raise KeyError("Unexpected key %s found in configuration file!"
                               % k)


def _save():
    logging.debug("Saving JSON Config to %s", os.path.join(_cdirs["config"],
                                                           CONFIG_FILENAME))
    with open(os.path.join(_cdirs["config"], CONFIG_FILENAME), "w") as f:
        json.dump(_config, f)


def init():
    """Initialize configuration values for server"""
    parser = argparse.ArgumentParser(description="Buttplug")
    parser.add_argument('--server_address', metavar='addr', type=str,
                        help='Address to listen on',
                        default=_config["server_address"])
    parser.add_argument('--websocket_address', metavar='websocket', type=str,
                        help='Enable websocket clients access via specified interface:port',
                        default=_config["websocket_address"])
    parser.add_argument('--config_dir', metavar='path', type=str,
                        help='configuration directory',
                        default=_cdirs["config"])
    parser.add_argument('--config_no_create_dir', action="store_true",
                        help='configuration directory')
    args = parser.parse_args()

    if args.config_dir:
        _cdirs["config"] = os.path.abspath(args.config_dir)
        _cdirs["plugin"] = os.path.join(_cdirs["config"], "plugins")
    if not os.path.exists(_cdirs["config"]):
        if args.config_no_create_dir:
            raise RuntimeError("Configuration directory does not exist!")
        logging.debug("Creating directory %s", _cdirs["config"])
        os.makedirs(_cdirs["config"])
    if not os.path.exists(os.path.join(_cdirs["config"], CONFIG_FILENAME)):
        _save()
    else:
        _load()
    if not os.path.exists(_cdirs["plugin"]):
        if args.config_no_create_dir:
            raise RuntimeError("Plugin directory does not exist!")
        logging.debug("Creating directory %s", _cdirs["plugin"])
        os.makedirs(_cdirs["plugin"])

    if args.server_address != _default_server_addr:
        set_value("server_address", args.server_address)

    if args.websocket_address != _default_wsserver_addr:
        set_value("websocket_address", args.websocket_address)


def get_value(key):
    """ Get a value from the config file """
    if key not in _config.keys():
        raise KeyError("Config value %s does not exist!" % key)
    logging.debug("Config value %s is %s", key, _config[key])
    return _config[key]


def set_value(key, value):
    """ Set a value, save config file """
    if key not in _config.keys():
        raise KeyError("Config value %s does not exist!" % key)
    _config[key] = value
    logging.debug("Setting config value %s to %s", key, _config[key])
    _save()


def get_dir(key):
    """ Get a directory path, either plugin or config """
    if key not in _cdirs.keys():
        raise KeyError("Config dir %s does not exist!" % key)
    logging.debug("Config dir %s is %s", key, _cdirs[key])
    return _cdirs[key]
