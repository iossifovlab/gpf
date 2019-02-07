from __future__ import print_function
from __future__ import unicode_literals

from functools import reduce

from pheno.common import MeasureType
from pheno.pheno_factory import PhenoFactory
from pheno_tool.pheno_common import PhenoFilterBuilder


class Dataset(object):

    def __init__(
            self, name, study_group, dataset_config):
        super(Dataset, self).__init__()
        genotype_browser = dataset_config.genotypeBrowser

        preview_columns = []
        download_columns = []
        pedigree_columns = {}
        pheno_columns = {}

        pedigree_selectors = []

        if genotype_browser:
            preview_columns = genotype_browser['previewColumns']
            download_columns = genotype_browser['downloadColumns']
            if genotype_browser['pedigreeColumns']:
                pedigree_columns =\
                    [s for pc in genotype_browser['pedigreeColumns']
                     for s in pc['slots']]
            if genotype_browser['phenoColumns']:
                pheno_columns = [s for pc in genotype_browser['phenoColumns']
                                 for s in pc['slots']]

        if dataset_config.pedigreeSelectors:
            pedigree_selectors = dataset_config.pedigreeSelectors

        self.name = name
        self.study_group = study_group

        self.dataset_config = dataset_config

        self.name = name
        self.preview_columns = preview_columns
        self.download_columns = download_columns
        self.pedigree_columns = pedigree_columns
        self.pheno_columns = pheno_columns

        self.pedigree_selectors = pedigree_selectors

        self.pheno_db = None
        self.pheno_filter_builder = None
        if self.pheno_db_name:
            self.pheno_db = PhenoFactory().get_pheno_db(self.pheno_db_name)

            pheno_filters = self.dataset_config.genotypeBrowser.phenoFilters
            if pheno_filters:
                self.pheno_filter_builder = PhenoFilterBuilder(self.pheno_db)


        if len(self.dataset_config.pedigreeSelectors) != 0:
            self.legend = {ps['id']: ps['domain'] + [ps['default']]
                           for ps in self.dataset_config.pedigreeSelectors}
        else:
            self.legend = {}

    @property
    def pheno_db_name(self):
        return self.dataset_config.phenoDB

    @property
    def id(self):
        return self.dataset_config.id

    @property
    def studies(self):
        return self.study_group.studies

    def transform_variants_kwargs(self, **kwargs):
        if 'pedigreeSelector' in kwargs:
            pedigree_selector_id = kwargs['pedigreeSelector']['id']
            pedigree_selectors = list(filter(
                lambda ps: ps['id'] == pedigree_selector_id,
                self.pedigree_selectors))
            if pedigree_selectors:
                pedigree_selector = pedigree_selectors[0]
                kwargs['pedigreeSelector']['source'] =\
                    pedigree_selector['source']

        return kwargs

    def get_variants(self, **kwargs):
        kwargs = self.transform_variants_kwargs(**kwargs)
        pheno_filter_args = kwargs.pop('phenoFilters', None)

        if pheno_filter_args:
            assert isinstance(pheno_filter_args, list)
            assert self.pheno_db
            assert self.pheno_filter_builder

            people_ids_to_query = self._transform_pheno_filters_to_people_ids(
                pheno_filter_args)
            people_ids_to_query = self._merge_with_people_ids(
                kwargs, people_ids_to_query)

            if len(people_ids_to_query) == 0:
                return

            kwargs['people_ids'] = list(people_ids_to_query)

        for variant in self.study_group.query_variants(**kwargs):

            variant = self._add_pheno_columns(variant)

            yield variant

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

        return reduce(set.intersection, people_ids)

    def _get_pheno_filter_constraints(self, pheno_filter):
        measure_type = MeasureType.from_str(pheno_filter['measureType'])
        selection = pheno_filter['selection']
        if measure_type in (MeasureType.continuous, MeasureType.ordinal):
            return tuple([selection['min'], selection['max']])
        return set(selection['values'])

    def _add_pheno_columns(self, variant):
        pheno_values = {}
        for pheno_column in self.pheno_columns:
            pheno_value = self.pheno_db.get_measure_values(
                pheno_column.source,
                family_ids=[variant.family.family_id],
                roles=[pheno_column.role])
            pheno_values[pheno_column.name] = ','.join(
                map(str, pheno_value.values()))

        for allele in variant.matched_alleles:
            allele.update_attributes(pheno_values)

        return variant


    @property
    def study_names(self):
        return self.study_group.study_names

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']

    def _get_legend_default_values(self):
        return [{
            'color': '#E0E0E0',
            'id': 'missing-person',
            'name': 'missing-person'
        }]

    def get_legend(self, *args, **kwargs):
        if 'pedigreeSelector' not in kwargs:
            legend = list(self.legend.values())[0] if self.legend else []
        else:
            legend = self.legend.get(kwargs['pedigreeSelector']['id'], [])

        return legend + self._get_legend_default_values()

    @property
    def order(self):
        return 0

    @staticmethod
    def _get_dataset_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    def _get_study_group_config_options(self, dataset_config):
        dataset_config['studyTypes'] = self.study_group.study_types
        dataset_config['genotypeBrowser']['hasStudyTypes'] =\
            self.study_group.has_study_types
        dataset_config['genotypeBrowser']['hasComplex'] =\
            self.study_group.has_complex
        dataset_config['genotypeBrowser']['hasCNV'] =\
            self.study_group.has_CNV
        dataset_config['genotypeBrowser']['hasDenovo'] =\
            self.study_group.has_denovo
        dataset_config['genotypeBrowser']['hasTransmitted'] =\
            self.study_group.has_transmitted
        dataset_config['studies'] =\
            self.study_group.study_names

        return dataset_config

    def get_dataset_description(self):
        keys = Dataset._get_dataset_description_keys()
        dataset_config = self.dataset_config.to_dict()

        dataset_config = self._get_study_group_config_options(dataset_config)

        return {key: dataset_config[key] for key in keys}
