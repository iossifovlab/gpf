
class StudyBase(object):

    def __init__(self, config):
        self.config = config

        self.id = self.config.id
        self.name = self.config.name
        self.phenotypes = self.config.phenotypes
        self.has_denovo = self.config.has_denovo
        self.has_transmitted = self.config.has_transmitted
        self.has_complex = self.config.has_complex
        self.has_cnv = self.config.has_cnv
        self.study_type = self.config.study_type
        self.year = self.config.year
        self.pub_med = self.config.pub_med
        self.description = self.config.description

        self.study_types = self.config.study_types
        self.years = self.config.years
        self.pub_meds = self.config.pub_meds
        self.order = self.config.order

    @property
    def families(self):
        raise NotImplementedError()

    def query_variants(self, **kwargs):
        raise NotImplementedError()

    def get_pedigree_values(self, column):
        raise NotImplementedError()


class Study(StudyBase):

    def __init__(self, config, backend):
        super(Study, self).__init__(config)

        self.backend = backend

    @property
    def families(self):
        return self.backend.families

    def query_variants(self, **kwargs):
        if 'studyFilters' in kwargs and \
                self.name not in kwargs['studyFilters']:
            return []
        else:
            return self.backend.query_variants(**kwargs)

    def get_pedigree_values(self, column):
        return set(self.backend.ped_df[column])
