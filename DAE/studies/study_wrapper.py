from __future__ import unicode_literals, print_function, absolute_import

import copy
import functools
from builtins import str

import os
import itertools

from RegionOperations import Region
from pheno.common import MeasureType
from pheno_tool.pheno_common import PhenoFilterBuilder
from utils.dae_utils import split_iterable
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
        pheno_columns = {}
        gene_weights_columns = []
        column_labels = {}

        pedigree_selectors = []

        if genotype_browser:
            preview_columns = genotype_browser['previewColumnsSlots']
            download_columns = genotype_browser['downloadColumnsSlots']
            if genotype_browser['phenoColumns']:
                pheno_columns = [s for pc in genotype_browser['phenoColumns']
                                 for s in pc['slots']]
            gene_weights_columns = genotype_browser['geneWeightsColumns']

            column_labels = genotype_browser['columnLabels']

        if 'pedigreeSelectors' in self.config:
            pedigree_selectors = self.config.pedigree_selectors

        self.preview_columns = preview_columns
        self.download_columns = download_columns
        self.pheno_columns = pheno_columns
        self.gene_weights_columns = gene_weights_columns
        self.column_labels = column_labels

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

            if self.config.genotypeBrowser:
                pheno_filters = self.config.genotypeBrowser.phenoFilters
                if pheno_filters:
                    self.pheno_filters_in_config = {
                        self._get_pheno_filter_key(pf.measureFilter)
                        for pf in pheno_filters
                        if pf['measureFilter']['filterType'] == 'single'
                    }
                    self.pheno_filter_builder = \
                        PhenoFilterBuilder(self.pheno_db)

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
    # callSet
    # minParentsCalled
    # ultraRareOnly
    # TMM_ALL
    def query_variants(self, weights_loader=None, **kwargs):
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

        if 'genomicScores'in kwargs:
            self._transform_genomic_scores(kwargs)

        if 'geneWeights' in kwargs:
            self._transform_gene_weights(weights_loader, kwargs)

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

        variants_from_studies = itertools.islice(
            self.study.query_variants(**kwargs), limit)

        for variant in self._add_pheno_columns(variants_from_studies):
            variant = self._add_roles_columns(variant)
            yield variant

    def _add_roles_columns(self, variant):
        genotype_browser = self.study.config.genotypeBrowser
        if isinstance(genotype_browser, bool) and genotype_browser is False:
            return variant
        # assert isinstance(genotype_browser, dict), type(genotype_browser)

        roles_columns = self.study.config.genotypeBrowser.rolesColumns

        if not roles_columns:
            return variant

        parsed_roles_columns = self._parse_roles_columns(roles_columns)

        for allele in variant.alt_alleles:
            roles_values = self._get_all_roles_values(
                allele, parsed_roles_columns)
            allele.update_attributes(roles_values)

        return variant

    def _parse_roles_columns(self, roles_columns):
        result = []
        for roles_column in roles_columns:
            roles_copy = copy.deepcopy(roles_column)
            roles = roles_copy.roles
            roles_copy.roles = [Role.from_name(role) for role in roles]

            result.append(roles_copy)

        return result

    def _get_all_roles_values(self, allele, roles_values):
        result = {}
        for roles_value in roles_values:
            result[roles_value.destination] = "".join(self._get_roles_value(
                allele, roles_value.roles))

        return result

    def _get_roles_value(self, allele, roles):
        result = []
        variant_in_members = allele.variant_in_members_objects

        for role in roles:
            for member in variant_in_members:
                if member.role == role:
                    result.append(str(role) + member.sex.short())

        return result

    def _add_pheno_columns(self, variants_iterable):
        genotype_browser = self.study.config.genotypeBrowser

        if self.pheno_db is None or \
                (isinstance(genotype_browser, bool) and
                 genotype_browser is False):
            for variant in variants_iterable:
                yield variant

        for variants_chunk in split_iterable(variants_iterable, 5000):
            families = {variant.family_id for variant in variants_chunk}

            pheno_column_values = self._get_all_pheno_values(families)

            for variant in variants_chunk:
                pheno_values = self._get_pheno_values_for_variant(
                    variant, pheno_column_values)
                for allele in variant.alt_alleles:
                    allele.update_attributes(pheno_values)

                yield variant

    def _get_pheno_values_for_variant(self, variant, pheno_column_values):
        pheno_values = {}

        for pheno_column_df, pheno_column_name in pheno_column_values:
            variant_pheno_value_df = pheno_column_df[
                pheno_column_df['person_id'].isin(variant.members_ids)]
            variant_pheno_value_df.set_index('person_id', inplace=True)
            assert len(variant_pheno_value_df.columns) == 1
            column = variant_pheno_value_df.columns[0]

            pheno_values[pheno_column_name] = ",".join(
                map(str, variant_pheno_value_df[column].tolist()))

        return pheno_values

    def _get_all_pheno_values(self, families):
        pheno_column_dfs = []
        pheno_column_names = []

        for pheno_column in self.config.genotypeBrowser.phenoColumns:
            for slot in pheno_column.slots:
                pheno_column_dfs.append(
                    self.pheno_db.get_measure_values_df(
                        slot.measure,
                        family_ids=list(families),
                        roles=[slot.role]))
                pheno_column_names.append(slot.source)

        return list(zip(pheno_column_dfs, pheno_column_names))

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

    def _transform_genomic_scores(self, kwargs):
        genomic_scores = kwargs.pop('genomicScores', [])

        genomic_scores_filter = [
            (score['metric'],
             (score['rangeStart'], score['rangeEnd']))
            for score in genomic_scores
            if score['rangeStart'] or score['rangeEnd']
        ]

        if 'real_attr_filter' not in kwargs:
            kwargs['real_attr_filter'] = []
        kwargs['real_attr_filter'] += genomic_scores_filter

    def _transform_gene_weights(self, weights_loader, kwargs):
        if not weights_loader:
            return

        gene_weights = kwargs.pop('geneWeights', {})

        weight_name = gene_weights.get('weight', None)
        range_start = gene_weights.get('rangeStart', None)
        range_end = gene_weights.get('rangeEnd', None)

        if weight_name and weight_name in weights_loader:
            weight = weights_loader[gene_weights.get('weight')]

            genes = weight.get_genes(range_start, range_end)

            if 'genes' not in kwargs:
                kwargs['genes'] = []

            kwargs['genes'] += list(genes)

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
        if not pedigree_selector_id:
            return self.pedigree_selectors[0]\
                if self.pedigree_selectors else {}

        pedigree_selector_with_id = list(filter(
            lambda pedigree_selector: pedigree_selector.get('id') ==
            pedigree_selector_id, self.pedigree_selectors))

        return pedigree_selector_with_id[0] \
            if pedigree_selector_with_id else {}

    def _get_dataset_config_options(self, config):
        config['studyTypes'] = self.config.study_types
        config['description'] = self.study.description

        return config

    @staticmethod
    def _get_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

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

            if self.pheno_db is None:
                continue

            measure = self.pheno_db.get_measure(
                measure_filter['measure'])
            measure_filter['domain'] = measure.values_domain.split(",")

    def get_column_labels(self):
        return self.column_labels

    def gene_sets_cache_file(self):
        cache_path = os.path.join(
            os.path.split(self.config.study_config.config_file)[0],
            'denovo-cache.json')

        return cache_path
