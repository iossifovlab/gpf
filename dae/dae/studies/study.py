class GenotypeData(object):

    def __init__(self, config, studies):
        self.config = config
        self.studies = studies

        self.id = self.config.id
        self.name = self.config.name
        self.description = self.config.description
        self.year = self.config.year
        self.pub_med = self.config.pub_med

        self.has_denovo = self.config.has_denovo
        self.has_transmitted = self.config.has_transmitted
        self.has_cnv = self.config.hasCNV
        self.has_complex = self.config.has_complex

        self.study_type = self.config.study_type
        self.study_types = self.config.study_types
        self.years = self.config.years
        self.pub_meds = self.config.pub_meds

    def query_variants(
            self, regions=None, genes=None, effect_types=None,
            family_ids=None, person_ids=None,
            inheritance=None, roles=None, sexes=None,
            variant_type=None, real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            study_filters=None,
            **kwargs):
        raise NotImplementedError()

    def get_studies_ids(self):
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


class GenotypeDataStudy(GenotypeData):

    def __init__(self, config, backend):
        super(GenotypeDataStudy, self).__init__(config, [self])

        self.backend = backend

    def query_variants(
            self, regions=None, genes=None, effect_types=None,
            family_ids=None, person_ids=None,
            inheritance=None, roles=None, sexes=None,
            variant_type=None, real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            study_filters=None,
            **kwargs):

        if len(kwargs):
            # FIXME This will remain so it can be used for discovering
            # when excess kwargs are passed in order to fix such cases.
            print('received excess keyword arguments when querying variants!')
            print('kwargs received: {}'.format(list(kwargs.keys())))

        if study_filters and self.name not in study_filters:
            return

        for variant in self.backend.query_variants(
                regions=regions,
                genes=genes,
                effect_types=effect_types,
                family_ids=family_ids,
                person_ids=person_ids,
                inheritance=inheritance,
                roles=roles,
                sexes=sexes,
                variant_type=variant_type,
                real_attr_filter=real_attr_filter,
                ultra_rare=ultra_rare,
                return_reference=return_reference,
                return_unknown=return_unknown,
                limit=limit
                ):
            for allele in variant.alleles:
                allele.update_attributes({'studyName': self.name})
            yield variant

    def get_studies_ids(self):
        return [self.id]

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
