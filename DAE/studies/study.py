class Study(object):

    def __init__(self, backend):
        self.backend = backend

    def filter_variants(self, **filter_args):
        return self.backend.filter_variants(**filter_args)
