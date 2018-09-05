class Study(object):

    def __init__(self, name, backend, study_config):
        self.name = name
        self.backend = backend

        self._phenotypes = study_config.phenotypes
        self._has_denovo = study_config.hasDenovo
        self._has_transmitted = study_config.hasTransmitted
        self._has_complex = study_config.hasComplex
        self._has_CNV = study_config.hasCNV
        self._study_type = study_config.studyType

    def query_variants(self, **kwargs):
        return self.backend.query_variants(**kwargs)

    # FIXME: fill these with real data

    @property
    def families(self):
        return self.backend.families

    @property
    def phenotypes(self):
        return self._phenotypes

    @property
    def has_denovo(self):
        return self._has_denovo

    @property
    def has_transmitted(self):
        return self._has_transmitted

    @property
    def has_complex(self):
        return self._has_complex

    @property
    def has_CNV(self):
        return self._has_CNV

    @property
    def study_type(self):
        return self._study_type

    @property
    def year(self):
        return None

    @property
    def pub_med(self):
        return None
