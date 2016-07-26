# Buttplug - DEPRECATED - See http://www.github.com/metafetish/buttplug #

This project has been _DEPRECATED_. I'm keeping the repo around for
reference, but it's been superceded by the Rust version of the project
at http://www.github.com/metafetish/buttplug.

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

## License ##

Buttplug is BSD licensed.

    Copyright (c) 2012-2013, Kyle Machulis/Nonpolynomial Labs
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
        * Redistributions of source code must retain the above copyright
          notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above copyright
          notice, this list of conditions and the following disclaimer in the
          documentation and/or other materials provided with the distribution.
        * Neither the name of the Kyle Machulis/Nonpolynomial Labs nor the
          names of its contributors may be used to endorse or promote products
          derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY Kyle Machulis/Nonpolynomial Labs ''AS IS'' AND ANY
    EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL Kyle Machulis/Nonpolynomial Labs BE LIABLE FOR ANY
    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
