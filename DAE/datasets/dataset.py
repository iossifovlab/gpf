from __future__ import print_function
from __future__ import unicode_literals
from builtins import map
from builtins import str

import itertools
import logging

from RegionOperations import Region
from variants.attributes import Role
from datasets.helpers import EFFECT_TYPES_MAPPING
from variants.attributes_query import role_query, variant_type_converter, \
    sex_converter, AndNode, NotNode, OrNode, ContainsNode

logger = logging.getLogger(__name__)


class Dataset(object):

    def __init__(
            self, name, study_group, dataset_config):
        super(Dataset, self).__init__()
        genotypeBrowser = dataset_config.genotypeBrowser
        preview_columns = []
        download_columns = []
        if genotypeBrowser:
            preview_columns = genotypeBrowser['previewColumns']
            download_columns = genotypeBrowser['downloadColumns']

        self.name = name
        self.study_group = study_group

        self.dataset_config = dataset_config

        self.name = name
        self.preview_columns = preview_columns
        self.download_columns = download_columns

        if len(self.dataset_config.pedigreeSelectors) != 0:
            self.legend = self.dataset_config.pedigreeSelectors[0]['domain']

    def get_variants(self, **kwargs):
        return self.study_group.get_variants(**kwargs)

    @property
    def study_names(self):
        return self.study_group.study_names

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']

    def get_legend(self, *args, **kwargs):
        return self.legend

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


class DatasetWrapper(Dataset):

    def __init__(self, *args, **kwargs):
        super(DatasetWrapper, self).__init__(*args, **kwargs)

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
    def get_variants(self, **kwargs):
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
            effect_types = kwargs['effect_types']
            effect_types = [
                EFFECT_TYPES_MAPPING[effect] for effect in effect_types
            ]
            kwargs['effect_types'] = [
                item for sublist in effect_types for item in sublist
            ]

        return itertools.islice(
            super(DatasetWrapper, self).get_variants(**kwargs), limit)

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
            kwargs['real_attr_filter'] = {}

        if value not in kwargs['real_attr_filter']:
            kwargs['real_attr_filter'][value] = []

        kwargs['real_attr_filter'][value].append(value_range)

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
