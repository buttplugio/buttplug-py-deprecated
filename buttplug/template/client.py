from buttplug.template import base


class BPClient(base.BPBase):

    def __init__(self):
        super(BPClient, self).__init__()
        self.socket_identity = self.random_ident()

    def register(self):
        self.send(["s", "BPRegisterClient", self.APP_NAME])
