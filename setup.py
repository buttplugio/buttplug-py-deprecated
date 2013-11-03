#!/usr/bin/env python

import sys

from cx_Freeze import setup, Executable
includes = ["zmq", "gevent", "greenlet", "msgpack"]

base = None
include_files = []
if sys.platform == "win32":
    # For the moment, just make this run as a console application on windows
    # base = "Win32GUI"

    # Hardcode the libzmq path because fuck it. Just make sure it gets copied on
    # windows.
    include_files.append(("c:/Python27/Lib/site-packages/pyzmq-13.0.0-py2.7-win32.egg/zmq/libzmq.pyd", "libzmq.pyd"))

setup(name='Buttplug',
      version='0.01',
      description='Buttplug Sex Toy Control Server',
      author='Kyle Machulis',
      author_email='kyle@nonpolynomial.com',
      url='http://www.feverything.com/',
      packages=['buttplug'],
      scripts=['scripts/buttplug', 'scripts/test-plugin', 'scripts/test-client'],
      options={"build_exe": {"includes": includes, "include_files": include_files}},
      executables=[Executable("scripts/buttplug", base=base), Executable("scripts/test-client", base=base), Executable("scripts/test-plugin", base=base)]
)
