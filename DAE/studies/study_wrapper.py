from __future__ import unicode_literals, print_function, absolute_import

import functools
from builtins import str

import os
import itertools

from RegionOperations import Region
from pheno.common import MeasureType
from pheno_tool.pheno_common import PhenoFilterBuilder
from variants.attributes import Role
from studies.helpers import expand_effect_types
from backends.attributes_query import role_query, variant_type_converter, \
    sex_converter, AndNode, NotNode, OrNode, ContainsNode


class StudyWrapper(object):

    def __init__(self, study, pheno_factory, *args, **kwargs):
        super(StudyWrapper, self).__init__(*args, **kwargs)
        self.study = study
        self._init_wdae_config()
        self.pheno_factory = pheno_factory
        self._init_pheno(self.pheno_factory)

    def _init_wdae_config(self):
        genotype_browser = self.config.genotypeBrowser

        preview_columns = []
        download_columns = []
        pedigree_columns = {}
        pheno_columns = {}

        pedigree_selectors = []

        if genotype_browser:
            preview_columns = genotype_browser['previewColumnsSlots']
            download_columns = genotype_browser['downloadColumnsSlots']
            if genotype_browser['pedigreeColumns']:
                pedigree_columns =\
                    [s for pc in genotype_browser['pedigreeColumns']
                     for s in pc['slots']]
            if genotype_browser['phenoColumns']:
                pheno_columns = [s for pc in genotype_browser['phenoColumns']
                                 for s in pc['slots']]

        if 'pedigreeSelectors' in self.config:
            pedigree_selectors = self.config.pedigree_selectors

        self.preview_columns = preview_columns
        self.download_columns = download_columns
        self.pedigree_columns = pedigree_columns
        self.pheno_columns = pheno_columns

        self.pedigree_selectors = pedigree_selectors

        if len(self.pedigree_selectors) != 0:
            self.legend = {
                ps['id']: ps['domain'] + [ps['default']]
                for ps in self.pedigree_selectors
            }
        else:
            self.legend = {}

    def _init_pheno(self, pheno_factory):
        self.pheno_db = None
        self.pheno_filter_builder = None

        self.pheno_filters_in_config = set()
        pheno_db = self.config.phenoDB
        if pheno_db:
            self.pheno_db = pheno_factory.get_pheno_db(pheno_db)

            pheno_filters = self.config.genotypeBrowser.phenoFilters
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

    def __getattr__(self, name):
        return getattr(self.study, name)

    FILTER_RENAMES_MAP = {
        'familyIds': 'family_ids',
        'gender': 'sexes',
        'geneSymbols': 'genes',
        'variantTypes': 'variant_type',
        'effectTypes': 'effect_types',
        'regionS': 'regions',
    }

    # Not implemented:
    # inChild
    # genomicScores
    # callSet
    # minParentsCalled
    # ultraRareOnly
    # TMM_ALL
    def query_variants(self, **kwargs):
        # print("kwargs in study group:", kwargs)
        kwargs = self._add_people_with_phenotype(kwargs)

        limit = None
        if 'limit' in kwargs:
            limit = kwargs['limit']

        if 'regions' in kwargs:
            kwargs['regions'] = list(map(Region.from_str, kwargs['regions']))

        if 'presentInChild' in kwargs:
            self._transform_present_in_child(kwargs)

        if 'presentInParent' in kwargs:
            self._transform_present_in_parent(kwargs)

        if 'minAltFrequencyPercent' in kwargs or \
                'maxAltFrequencyPercent' in kwargs:
            self._transform_min_max_alt_frequency(kwargs)

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        if 'sexes' in kwargs:
            sexes = kwargs['sexes']
            sexes = [ContainsNode(sex_converter(sex)) for sex in sexes]
            kwargs['sexes'] = OrNode(sexes)

        if 'variant_type' in kwargs:
            variant_types = kwargs['variant_type']
            variant_types = [ContainsNode(variant_type_converter(t))
                             for t in variant_types]
            kwargs['variant_type'] = OrNode(variant_types)

        if 'effect_types' in kwargs:
            kwargs['effect_types'] = expand_effect_types(
                kwargs['effect_types'])

        if 'studyFilters' in kwargs:
            if kwargs['studyFilters']:
                kwargs['studyFilters'] =\
                    [sf['studyName'] for sf in kwargs['studyFilters']]
            else:
                del(kwargs['studyFilters'])

        pheno_filter_args = kwargs.pop('phenoFilters', None)

        if pheno_filter_args:
            assert isinstance(pheno_filter_args, list)
            assert self.pheno_db

            people_ids_to_query = self._transform_pheno_filters_to_people_ids(
                pheno_filter_args)
            people_ids_to_query = self._merge_with_people_ids(
                kwargs, people_ids_to_query)

            if len(people_ids_to_query) == 0:
                return

            kwargs['person_ids'] = list(people_ids_to_query)

        for variant in itertools.islice(
                self.study.query_variants(**kwargs),
                limit):

            variant = self._add_pheno_columns(variant)

            yield variant

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
        people_ids_filter = kwargs.pop('person_ids', None)
        result = people_ids_to_query
        if people_ids_filter is not None:
            result = people_ids_to_query.intersection(people_ids_filter)

        return result

    def _transform_pheno_filters_to_people_ids(self, pheno_filter_args):
        people_ids = []
        for pheno_filter_arg in pheno_filter_args:
            if not self.pheno_db.has_measure(pheno_filter_arg['measure']):
                continue
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
        return set(selection['selection'])

    def _add_people_with_phenotype(self, kwargs):
        people_with_phenotype = set()
        if 'pedigreeSelector' in kwargs and\
                kwargs['pedigreeSelector'] is not None:
            pedigree_selector_query = kwargs.pop('pedigreeSelector')

            pedigree_selector = self.get_pedigree_selector(
                pedigree_selector_query['id'])

            for family in self.families.values():
                family_members_with_phenotype = set(
                    [person.person_id for person in
                        family.get_people_with_phenotypes(
                            pedigree_selector['source'],
                            pedigree_selector_query['checkedValues'])])
                people_with_phenotype.update(family_members_with_phenotype)

            if 'person_ids' in kwargs:
                people_with_phenotype.intersection(kwargs['person_ids'])

            kwargs['person_ids'] = list(people_with_phenotype)

        return kwargs

    def _transform_min_max_alt_frequency(self, kwargs):
        min_value = None
        max_value = None

        if 'minAltFrequencyPercent' in kwargs:
            min_value = kwargs['minAltFrequencyPercent']
            kwargs.pop('minAltFrequencyPercent')

        if 'maxAltFrequencyPercent' in kwargs:
            max_value = kwargs['maxAltFrequencyPercent']
            kwargs.pop('maxAltFrequencyPercent')

        value_range = (min_value, max_value)

        if value_range == (None, None):
            return

        if value_range[0] is None:
            value_range = (float('-inf'), value_range[1])

        if value_range[1] is None:
            value_range = (value_range[0], float('inf'))

        print(value_range)

        value = 'af_allele_freq'
        if 'real_attr_filter' not in kwargs:
            kwargs['real_attr_filter'] = []

        kwargs['real_attr_filter'].append((value, value_range))

    def _transform_present_in_child(self, kwargs):
        roles_query = []

        for filter_option in kwargs['presentInChild']:
            new_roles = None

            if filter_option == 'affected only':
                new_roles = AndNode([
                    ContainsNode(Role.prb),
                    NotNode(ContainsNode(Role.sib))
                ])

            if filter_option == 'unaffected only':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.prb)),
                    ContainsNode(Role.sib)
                ])

            if filter_option == 'affected and unaffected':
                new_roles = AndNode([
                    ContainsNode(Role.prb),
                    ContainsNode(Role.sib)
                ])

            if filter_option == 'neither':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.prb)),
                    NotNode(ContainsNode(Role.sib))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInChild')

        if not roles_query:
            return

        roles_query = OrNode(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles)
            kwargs['roles'] = AndNode([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query

    def _transform_present_in_parent(self, kwargs):
        roles_query = []

        for filter_option in kwargs['presentInParent']:
            new_roles = None

            if filter_option == 'mother only':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.dad)),
                    ContainsNode(Role.mom)
                ])

            if filter_option == 'father only':
                new_roles = AndNode([
                    ContainsNode(Role.dad),
                    NotNode(ContainsNode(Role.mom))
                ])

            if filter_option == 'mother and father':
                new_roles = AndNode([
                    ContainsNode(Role.dad),
                    ContainsNode(Role.mom)
                ])

            if filter_option == 'neither':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.dad)),
                    NotNode(ContainsNode(Role.mom))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInParent')

        if not roles_query:
            return

        roles_query = OrNode(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles)
            kwargs['roles'] = AndNode([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query

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

    def get_pedigree_selector(self, pedigree_selector_id):
        pedigree_selector_with_id = list(filter(
            lambda pedigree_selector: pedigree_selector.get('id') ==
            pedigree_selector_id, self.pedigree_selectors))

        return pedigree_selector_with_id[0] \
            if pedigree_selector_with_id else {}

    # FIXME:
    def _get_dataset_config_options(self, config):
        config['studyTypes'] = self.config.study_types
        config['description'] = self.study.description
        # config['studies'] = self.config.names

        print(self.config.genotype_browser)

        # config['genotypeBrowser']['hasStudyTypes'] =\
        #     self.config.has_study_types
        # config['genotypeBrowser']['hasComplex'] =\
        #     self.config.has_complex
        # config['genotypeBrowser']['hasCNV'] =\
        #     self.config.has_CNV

        return config

    @staticmethod
    def _get_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    # FIXME:
    def get_dataset_description(self):
        keys = self._get_description_keys()
        config = self.config.to_dict()

        config = self._get_dataset_config_options(config)

        result = {key: config.get(key, None) for key in keys}

        self._augment_pheno_filters_domain(result)

        return result

    def _augment_pheno_filters_domain(self, dataset_description):
        genotype_browser = dataset_description.get('genotypeBrowser', None)
        if not genotype_browser:
            return

        pheno_filters = genotype_browser.get('phenoFilters', None)
        if not pheno_filters:
            return

        for pheno_filter in pheno_filters:
            measure_filter = pheno_filter.get('measureFilter', None)
            if measure_filter is None or 'measure' not in measure_filter:
                continue

            if getattr(self.study, 'pheno_db', None) is None:
                continue

            measure = self.study.pheno_db.get_measure(
                measure_filter['measure'])
            measure_filter['domain'] = measure.values_domain.split(",")

    def gene_sets_cache_file(self):
        cache_filename = '{}.json'.format(self.id)
        cache_path = os.path.join(
            os.path.split(self.config.study_config.config_file)[0],
            'denovo-cache/' + cache_filename)

        return cache_path
