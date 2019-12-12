import itertools
import functools

from dae.studies.study import GenotypeData


class GenotypeDataGroup(GenotypeData):

    def __init__(self, genotype_data_group_config, studies):
        super(GenotypeDataGroup, self).__init__(
            genotype_data_group_config,
            studies
        )

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

    @property
    def families(self):
        return functools.reduce(
            lambda x, y: self._combine_families(x, y),
            [genotype_data_study.families
             for genotype_data_study in self.studies]
        )

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

    def get_people_from_people_group(
            self, people_group_id, people_group_value):
        return functools.reduce(
            lambda x, y: x | y,
            [st.get_people_from_people_group(
             people_group_id, people_group_value) for st in self.studies],
            set()
        )
