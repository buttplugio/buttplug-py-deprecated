import gevent
from gevent_zeromq import zmq
import sys
import random


def server(context):
    s = context.socket(zmq.ROUTER)
    s.bind('inproc://queue')
    while True:
        print "send"
        identity = s.recv()
        data = s.recv()
        print "%s %s" % (identity, data)
        s.send(identity, zmq.SNDMORE)
        s.send("what")


def client(context):
    c = context.socket(zmq.DEALER)
    sind = random.randrange(100)
    c.setsockopt(zmq.IDENTITY, "%d" % sind)
    print("Identity : %d" % sind)
    c.connect('inproc://queue')
    for i in range(0, 5):
        c.send("test")
        msg = c.recv()
        gevent.sleep(1)
    c.close()


def main():
    context = zmq.Context()
    gevent.spawn(server, context)
    for i in range(0, 5):
        gevent.spawn(client, context)
    while True:
        gevent.sleep(1)


if __name__ == '__main__':
    sys.exit(main())
