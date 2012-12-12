## Linux (assuming debian/ubuntu)

* apt-get install libusb-1.0-0-dev libevent-dev

## OS X

* brew install python libusb libevent

## All platforms after above steps

* pip install gevent msgpack-python cython
* git clone git://github.com/qdot/cython-hidapi
* cd cython-hidapi
* git submodule update --init
* python setup-mac.py build
* python setup-mac.py install
