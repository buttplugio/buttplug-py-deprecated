from fuckeverything.template import base


class FEClient(base.FEBase):

    def __init__(self):
        super(FEClient, self).__init__()

    def register(self):
        self.send(["s", "FERegisterClient", self.APP_NAME])
