import itertools
import functools
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.families_groups import FamiliesGroups


class GenotypeData:

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
        self.families_groups = None

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

    # def get_people_from_people_group(self, people_group, people_group_value):
    #     raise NotImplementedError()

    def _build_study_groups(self):
        if self.families_groups is None:
            config = self.config.people_group_config['peopleGroup']
            self.families_groups = FamiliesGroups.from_config(
                self.families, config.keys(), config
            )
            self.families_groups.add_predefined_groups([
                'status', 'role', 'sex'
            ])

    def get_families_group(self, families_group_id):
        self._build_study_groups()
        return self.families_groups.get(families_group_id)

    # def get_people_from_people_group(
    #         self, people_group_id, people_group_values):
    #     families_group = self.get_people_group(people_group_id)
    #     persons = families_group.get_people_with_propvalues(
    #         people_group_values)
    #     return set([p.person_id for p in persons])        
    #     # source = people_group.source

    #     # pedigree_df = self._backend.families.ped_df
    #     # people_ids = pedigree_df[
    #     #     pedigree_df[source].apply(str) == str(people_group_value)]

    #     # return set(people_ids['person_id'])

    def _get_person_color(self, person, people_group):
        if person.generated:
            return '#E0E0E0'
        # print(people_group)

        if people_group is None:
            return '#FFFFFF'
        return people_group.person_color(person)


class GenotypeDataGroup(GenotypeData):

    def __init__(self, genotype_data_group_config, studies):
        super(GenotypeDataGroup, self).__init__(
            genotype_data_group_config,
            studies
        )
        self._families = self._build_families()

    @property
    def families(self):
        return self._families

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
        return itertools.chain(*[
                genotype_data_study.query_variants(
                    regions, genes, effect_types, family_ids,
                    person_ids, inheritance, roles, sexes, variant_type,
                    real_attr_filter, ultra_rare, return_reference,
                    return_unknown, limit, study_filters, **kwargs
                )
                for genotype_data_study in self.studies
            ])

    def get_studies_ids(self):
        # TODO Use the 'cached' property on this
        return [genotype_data_study.id for genotype_data_study in self.studies]

    def _build_families(self):
        return FamiliesData.from_families(functools.reduce(
            lambda x, y: self._combine_families(x, y),
            [genotype_data_study.families
             for genotype_data_study in self.studies]
        ))

    def _combine_families(self, first, second):
        same_families = set(first.keys()) & set(second.keys())
        combined_dict = {}
        combined_dict.update(first)
        combined_dict.update(second)
        for sf in same_families:
            combined_dict[sf] =\
                first[sf] if len(first[sf]) > len(second[sf]) else second[sf]
        return combined_dict

    def get_pedigree_values(self, column):
        return functools.reduce(
            lambda x, y: x | y,
            [st.get_pedigree_values(column) for st in self.studies], set())

    # def get_people_from_people_group(
    #         self, people_group_id, people_group_value):
    #     return functools.reduce(
    #         lambda x, y: x | y,
    #         [st.get_people_from_people_group(
    #          people_group_id, people_group_value) for st in self.studies],
    #         set()
    #     )


class GenotypeDataStudy(GenotypeData):

    def __init__(self, config, backend):
        super(GenotypeDataStudy, self).__init__(config, [self])

        self._backend = backend

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

        for variant in self._backend.query_variants(
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
        return self._backend.families

    def get_pedigree_values(self, column):
        return set(self._backend.families.ped_df[column])
