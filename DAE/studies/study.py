class Study(object):

    def __init__(self, name, backend, study_config):
        self.name = name
        self.backend = backend
        self.study_config = study_config

    def query_variants(self, **kwargs):
        return self.backend.query_variants(**kwargs)

    # FIXME: fill these with real data

    @property
    def families(self):
        return self.backend.families

    @property
    def phenotypes(self):
        return self.study_config.phenotypes

    @property
    def has_denovo(self):
        return self.study_config.hasDenovo

    @property
    def has_transmitted(self):
        return self.study_config.hasTransmitted

    @property
    def has_complex(self):
        return self.study_config.hasComplex

    @property
    def has_CNV(self):
        return self.study_config.hasCNV

    @property
    def study_type(self):
        return self.study_config.studyType

    @property
    def year(self):
        return None

    @property
    def pub_med(self):
        return None
