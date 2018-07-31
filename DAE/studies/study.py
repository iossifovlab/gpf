class Study(object):

    def __init__(self, backend):
        self.backend = backend

    def query_variants(self, **kwargs):
        return self.backend.query_variants(**kwargs)
