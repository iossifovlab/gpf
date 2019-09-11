class StudyBase(object):

    def __init__(self, config, studies):
        self.config = config
        self.studies = studies

        self.id = self.config.id
        self.name = self.config.name
        self.has_denovo = self.config.has_denovo
        self.has_transmitted = self.config.has_transmitted
        self.has_complex = self.config.has_complex
        self.has_cnv = self.config.hasCNV
        self.study_type = self.config.study_type
        self.year = self.config.year
        self.pub_med = self.config.pub_med

        self.study_types = self.config.study_types
        self.years = self.config.years
        self.pub_meds = self.config.pub_meds

        self.description = self.config.description

        self.study_names = ','.join(study.name for study in self.studies)

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
        if not self.config.people_group_config and \
                not self.config.people_group_config.people_group:
            return None

        people_groups = self.config.people_group_config.people_group
        if not people_group_id:
            return people_groups.values()[0] if people_groups else {}

        people_group_with_id = people_groups.get(people_group_id, {})

        return people_group_with_id


class Study(StudyBase):

    def __init__(self, config, backend):
        super(Study, self).__init__(config, [self])

        self.backend = backend

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

    def get_people_with_people_group(
            self, people_group_id, people_group_value):
        people_group = self.get_people_group(people_group_id)
        source = people_group.source

        pedigree_df = self.backend.ped_df
        people_ids = pedigree_df[
            pedigree_df[source].apply(str) == str(people_group_value)]

        return set(people_ids['person_id'])
