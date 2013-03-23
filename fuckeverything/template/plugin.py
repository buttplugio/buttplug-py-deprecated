from fuckeverything.template import base


class FEPlugin(base.FEBase):

    def __init__(self):
        super(FEPlugin, self).__init__()
        self.count_mode = False
        self.device_id = None
        self.add_handlers({"FEPluginOpenDevice": self.open_device,
                           "FEPluginReleaseDevice": self.release_device})

    def setup_parser(self):
        super(FEPlugin, self).setup_parser()
        self.parser.add_argument('--count', action='store_true', help="count mode "
                                 "means that process will only be used to keep device "
                                 "counts")
        self.parser.add_argument('--identity', action='store', type=str, required=True,
                                 help="server provided zmq socket identity")

    def get_device_list(self):
        raise RuntimeError("Define your own damn get_device_list!")

    def parse_arguments(self):
        r = super(FEPlugin, self).parse_arguments()
        if not r:
            return r
        if self.args.count is True:
            self.count_mode = True
        self.socket_identity = self.args.identity
        return True

    def register(self):
        if self.count_mode:
            self.send(["s", "FEPluginRegisterCount", self.APP_NAME])
        else:
            self.send(["s", "FEPluginRegisterClaim", self.APP_NAME])

    def release_device(self, msg):
        raise RuntimeError("Define your own damn release_device!")

    def open_device(self, msg):
        raise RuntimeError("Define your own damn open_device!")
