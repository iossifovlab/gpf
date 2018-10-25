class Study(object):

    def __init__(self, name, backend, study_config):
        self.name = name
        self.backend = backend
        self.study_config = study_config

    def query_variants(self, **kwargs):
        study_types_filter = kwargs.get('studyTypes', None)
        if study_types_filter:
            print("StudyTypes filtered...", study_types_filter, self.study_type)
            # FIXME: lowercase vs uppercase
            # if self.study_type not in study_types_filter:
            #     return []

        return self.backend.query_variants(**kwargs)

    def get_phenotype_values(self, pheno_column):
        return set(self.backend.ped_df[pheno_column])

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

    # FIXME: fill these with real data

    @property
    def year(self):
        return None

    @property
    def pub_med(self):
        return None
