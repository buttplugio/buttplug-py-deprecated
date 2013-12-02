# Buttplug - config module
# Copyright (c) Kyle Machulis/Nonpolynomial Labs, 2012-2013
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the <ORGANIZATION> nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""BP stores its configuration on disk as a JSON file (defaulting to
~/.buttplug as the storage directory.). When the BP process is started, it
loads this file, checks validity against an expected schema, and creates an
object that can be accessed by BP components. Each time a value is set in the
config, it is serialized to disk.

"""

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
    """Load JSON config file into a python dict, checking validity against
    expected values.

    """
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
    """Save the config dict to a JSON file on disk"""
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
