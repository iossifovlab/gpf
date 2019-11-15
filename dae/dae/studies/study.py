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

    def _get_person_color(self, person, people_group):
        if person.generated:
            return '#E0E0E0'
        if len(people_group) == 0:
            return '#FFFFFF'

        source = people_group['source']
        people_group_attribute = person.get_attr(source)
        domain = people_group['domain'].get(people_group_attribute, None)

        if domain and people_group_attribute:
            return domain['color']
        else:
            return people_group['default']['color']


class Study(StudyBase):

    def __init__(self, config, backend):
        super(Study, self).__init__(config, [self])

        self.backend = backend

    def query_variants(self, **kwargs):
        if 'studyFilters' in kwargs and \
                self.name not in kwargs['studyFilters']:
            return
        else:
            for variant in self.backend.query_variants(
                    regions=kwargs.get('regions'),
                    genes=kwargs.get('genes'),
                    effect_types=kwargs.get('effect_types'),
                    family_ids=kwargs.get('family_ids'),
                    person_ids=kwargs.get('person_ids'),
                    inheritance=kwargs.get('inheritance'),
                    roles=kwargs.get('roles'),
                    sexes=kwargs.get('sexes'),
                    variant_type=kwargs.get('variant_type'),
                    real_attr_filter=kwargs.get('real_attr_filter'),
                    ultra_rare=kwargs.get('ultra_rare'),
                    return_reference=kwargs.get('return_reference'),
                    return_unknown=kwargs.get('return_unknown'),
                    limit=kwargs.get('limit')
                    ):
                for allele in variant.alleles:
                    allele.update_attributes({'studyName': self.name})
                yield variant

    @property
    def families(self):
        return self.backend.families.families

    def get_pedigree_values(self, column):
        return set(self.backend.families.ped_df[column])

    def get_people_with_people_group(
            self, people_group_id, people_group_value):
        people_group = self.get_people_group(people_group_id)
        source = people_group.source

        pedigree_df = self.backend.families.ped_df
        people_ids = pedigree_df[
            pedigree_df[source].apply(str) == str(people_group_value)]

        return set(people_ids['person_id'])
