import os.path


class StudyBase(object):

    def __init__(self, config):
        self.config = config

        self.id = self.config.id
        self.name = self.config.name
        # self.phenotypes = self.config.phenotypes
        self.has_denovo = self.config.get('hasDenovo', None)
        self.has_transmitted = self.config.get('hasTransmitted', None)
        self.has_complex = self.config.get('hasComplex', None)
        self.has_cnv = self.config.get('hasCNV', None)
        self.study_type = self.config.get('studyType', None)
        self.year = self.config.get('year', None)
        self.pub_med = self.config.get('pub_med', '')

        if os.path.exists(self.config.description):
            with open(self.config.description) as desc:
                self.description = desc.read()
        else:
            self.description = self.config.description

    @property
    def years(self):
        return [self.config.year] if self.config.year else []

    @property
    def pub_meds(self):
        return [self.config.pub_med] if self.config.pub_med else []

    @property
    def study_types(self):
        return {self.config.study_type} \
            if self.config.get('studyType', None) else set()

    @property
    def ids(self):
        return [self.config.id]

    @property
    def names(self):
        return [self.config.name]

    def query_variants(self, **kwargs):
        raise NotImplementedError()

    @property
    def families(self):
        raise NotImplementedError()

    def get_pedigree_values(self, column):
        raise NotImplementedError()

    def get_people_with_people_group(self, people_group, people_group_value):
        raise NotImplementedError()

    def get_people_group(self, people_group_id):
        if 'peopleGroupConfig' not in self.config and \
                'peopleGroup' not in self.config.people_group_config:
            return None

        people_groups = self.config.people_group_config.people_group
        if not people_group_id:
            return people_groups[0] if people_groups else {}

        people_group_with_id = list(filter(
            lambda people_group: people_group.get('id') == people_group_id,
            people_groups))

        return people_group_with_id[0] if people_group_with_id else {}


class Study(StudyBase):

    def __init__(self, config, backend):
        super(Study, self).__init__(config)

        self.backend = backend

        self.studies = [self]
        self.study_names = ",".join(study.name for study in self.studies)

    def query_variants(self, **kwargs):
        if 'studyFilters' in kwargs and \
                self.name not in kwargs['studyFilters']:
            return
        else:
            for variant in self.backend.query_variants(**kwargs):
                for allele in variant.alleles:
                    allele.update_attributes({'studyName': self.name})
                yield variant

    @property
    def families(self):
        return self.backend.families

    def get_pedigree_values(self, column):
        return set(self.backend.ped_df[column])

    def get_people_with_people_group(self, people_group, people_group_value):
        pedigree_df = self.backend.ped_df
        people_ids = pedigree_df[
            pedigree_df[people_group].apply(str) == str(people_group_value)]

        return set(people_ids['person_id'])
