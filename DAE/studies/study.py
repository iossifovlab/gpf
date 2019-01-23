
class StudyBase(object):

    def __init__(self, name, config):
        self.name = name
        self.config = config

        self.id = self.config.id
        self.phenotypes = self.config.phenotypes
        self.has_denovo = self.config.has_denovo
        self.has_transmitted = self.config.has_transmitted
        self.has_complex = self.config.has_complex
        self.has_cnv = self.config.has_cnv
        self.study_type = self.config.study_type
        self.study_types = [self.study_type]

        self.year = self.config.year
        self.years = [self.year] if self.year is not None else None
        self.pub_med = self.config.pub_med
        self.pub_meds = [self.pub_med] if self.pub_med is not None else None

    def query_variants(self, **kwargs):
        return self.backend.query_variants(**kwargs)

    def get_phenotype_values(self, pheno_column='phenotype'):
        return set(self.backend.ped_df[pheno_column])

    @staticmethod
    def _get_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    @property
    def order(self):
        return 0

    def get_pedigree_values(self, column):
        return set(self.backend.ped_df[column])

    @property
    def families(self):
        return self.backend.families

    @property
    def description(self):
        return self.config.description


class Study(StudyBase):

    def __init__(self, name, backend, config):
        super(Study, self).__init__(name, config)

        self.backend = backend
        self._study_type_lowercase = self.study_type.lower()
