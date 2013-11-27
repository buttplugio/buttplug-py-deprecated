# Buttplug #

By Kyle Machulis <kyle@nonpolynomial.com>

## Overview ##

Buttplug is a framework for hooking up hardware to interfaces, where
hardware usually means sex toys, but could honestly be just about
anything. It's basically a userland HID manager for things that may
not specifically be HID.

The core of buttplug works as a router. It allows plugins that talk to
different hardware to register themselves, and clients to claim and
interact with the hardware. All of this is done via IPC, so while the
router is written in python, that both clients and plugins can be
written in the language of the implementors choice, assuming that
language has ZeroMQ bindings.

In depth information about architecture choices and framework usage
are available in
[the Buttplug documentation](http://github.com/feverything/buttplug/docs/design.org).

## Requirements for Development ##

For usage, Buttplug will usually be compiled into a distributable
platform specific binary via cxFreeze. However, if you would like to
work on the router itself, you'll need the following

- Python 2.7
- A working C++ compiler (for compiling bindings)
- pip
- virtualenv (optional but ever so handy)

Just create a new virtualenv, then run

    pip install -r requirements.txt

This should install and compile the needed bindings.
