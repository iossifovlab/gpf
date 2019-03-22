import os.path


class StudyBase(object):

    def __init__(self, config):
        self.config = config

        self.id = self.config.id
        self.name = self.config.name
        # self.phenotypes = self.config.phenotypes
        self.has_denovo = self.config.has_denovo
        self.has_transmitted = self.config.has_transmitted
        self.has_complex = self.config.has_complex
        self.has_cnv = self.config.has_cnv
        self.study_type = self.config.study_type
        self.year = self.config.year
        self.pub_med = self.config.pub_med

        if os.path.exists(self.config.description):
            with open(self.config.description) as desc:
                self.description = desc.read()
        else:
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

        self.studies = [self]
        self.study_names = ",".join(study.name for study in self.studies)

    @property
    def families(self):
        return self.backend.families

    def query_variants(self, **kwargs):
        if 'studyFilters' in kwargs and \
                self.name not in kwargs['studyFilters']:
            return []
        else:
            for variant in self.backend.query_variants(**kwargs):
                for allele in variant.alleles:
                    allele.update_attributes({'studyName': self.name})
                yield variant

    def get_pedigree_values(self, column):
        return set(self.backend.ped_df[column])
