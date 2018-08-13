class Study(object):

    def __init__(self, name, backend):
        self.name = name
        self.backend = backend

    def query_variants(self, **kwargs):
        return self.backend.query_variants(**kwargs)

    # FIXME: fill these with real data

    @property
    def families(self):
        return self.backend.families

    @property
    def has_denovo(self):
        return True

    @property
    def has_transmitted(self):
        return False

    @property
    def phenotypes(self):
        return {'autism'}

    @property
    def type(self):
        return None

    @property
    def year(self):
        return None

    @property
    def pub_med(self):
        return None
