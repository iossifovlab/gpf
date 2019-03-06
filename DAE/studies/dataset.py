from __future__ import print_function
from __future__ import unicode_literals

import os
import itertools
import functools

from pheno.common import MeasureType
from pheno.pheno_factory import PhenoFactory
from pheno_tool.pheno_common import PhenoFilterBuilder
from studies.study import StudyBase


class Dataset(StudyBase):

    def __init__(self, dataset_config, studies):
        super(Dataset, self).__init__(dataset_config)
        self.studies = studies
        self.study_names = ",".join(study.name for study in self.studies)

        self._init_pheno()

    def _init_pheno(self):
        self.pheno_db = None
        self.pheno_filter_builder = None

        self.pheno_filters_in_config = set()
        pheno_db = self.config.phenoDB
        if pheno_db:
            self.pheno_db = PhenoFactory().get_pheno_db(pheno_db)

            pheno_filters = self.config.genotypeBrowser.phenoFilters
            print(pheno_filters)
            self.pheno_filters_in_config = {
                self._get_pheno_filter_key(pf.measureFilter)
                for pf in pheno_filters
                if pf['measureFilter']['filterType'] == 'single'
            }

            if pheno_filters:
                self.pheno_filter_builder = PhenoFilterBuilder(self.pheno_db)

    @staticmethod
    def _get_pheno_filter_key(pheno_filter, measure_key='measure'):
        return '{}.{}'.format(pheno_filter['role'], pheno_filter[measure_key])

    def query_variants(self, **kwargs):
        pheno_filter_args = kwargs.pop('phenoFilters', None)

        if pheno_filter_args:
            assert isinstance(pheno_filter_args, list)
            assert self.pheno_db
            # assert self.pheno_filter_builder

            pheno_filter_args = self._filter_pheno_args(pheno_filter_args)

            people_ids_to_query = self._transform_pheno_filters_to_people_ids(
                pheno_filter_args)
            people_ids_to_query = self._merge_with_people_ids(
                kwargs, people_ids_to_query)

            if len(people_ids_to_query) == 0:
                return

            kwargs['people_ids'] = list(people_ids_to_query)

        for variant in itertools.chain(*[
                study.query_variants(**kwargs) for study in self.studies]):

            variant = self._add_pheno_columns(variant)
            yield variant

    def _filter_pheno_args(self, pheno_filters):
        result = []
        for pheno_filter in pheno_filters:
            pheno_filter_key = self._get_pheno_filter_key(pheno_filter)
            if pheno_filter_key in self.pheno_filters_in_config:
                result.append(pheno_filter)
        return result

    def _add_pheno_columns(self, variant):
        if self.pheno_db is None:
            return variant
        pheno_values = {}

        for pheno_column in self.config.genotypeBrowser.phenoColumns:
            for slot in pheno_column.slots:
                pheno_value = self.pheno_db.get_measure_values(
                    slot.measure,
                    family_ids=[variant.family.family_id],
                    roles=[slot.role])
                key = slot.source
                pheno_values[key] = ','.join(
                    map(str, pheno_value.values()))

        for allele in variant.alt_alleles:
            allele.update_attributes(pheno_values)

        return variant

    def _merge_with_people_ids(self, kwargs, people_ids_to_query):
        people_ids_filter = kwargs.pop('people_ids', None)
        if people_ids_filter is not None:
            people_ids_to_query = people_ids_to_query \
                .intersection(people_ids_filter)

        return people_ids_to_query

    def _transform_pheno_filters_to_people_ids(self, pheno_filter_args):
        people_ids = []
        for pheno_filter_arg in pheno_filter_args:
            pheno_constraints = self._get_pheno_filter_constraints(
                pheno_filter_arg)

            pheno_filter = self.pheno_filter_builder.make_filter(
                pheno_filter_arg['measure'], pheno_constraints)

            measure_df = self.pheno_db.get_measure_values_df(
                pheno_filter_arg['measure'],
                roles=[pheno_filter_arg["role"]])

            measure_df = pheno_filter.apply(measure_df)

            people_ids.append(set(measure_df['person_id']))

        if not people_ids:
            return set()

        return functools.reduce(set.intersection, people_ids)

    def _get_pheno_filter_constraints(self, pheno_filter):
        measure_type = MeasureType.from_str(pheno_filter['measureType'])
        selection = pheno_filter['selection']
        if measure_type in (MeasureType.continuous, MeasureType.ordinal):
            return tuple([selection['min'], selection['max']])
        return set(selection['values'])

    @property
    def families(self):
        return functools.reduce(
            lambda x, y: self._combine_families(x, y),
            [study.families for study in self.studies])

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

    def gene_sets_cache_file(self):
        cache_filename = '{}.json'.format(self.id)
        cache_path = os.path.join(
            os.path.split(self.config.study_config.config_file)[0],
            'denovo-cache/' + cache_filename)

        return cache_path

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']
