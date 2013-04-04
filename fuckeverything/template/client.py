from fuckeverything.template import base


class FEClient(base.FEBase):

    def __init__(self):
        super(FEClient, self).__init__()
        self.socket_identity = self.random_ident()

    def register(self):
        self.send(["s", "FERegisterClient", self.APP_NAME])
