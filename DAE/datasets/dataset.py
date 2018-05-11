from __future__ import print_function
import itertools
import logging

from RegionOperations import Region
from variants.attributes import Role
from helpers import EFFECT_TYPES_MAPPING
from variants.attributes_query_builder import token, and_node, not_node, or_node
from variants.attributes_query import role_query, variant_type_converter, \
    sex_converter

logger = logging.getLogger(__name__)


class Dataset(object):

    def __init__(self, name, variants, preview_columns=None, download_columns=None):
        if preview_columns is None:
            preview_columns = []

        if download_columns is None:
            download_columns = []

        self._variants = variants

        self.name = name
        self.preview_columns = preview_columns
        self.download_columns = download_columns

    def get_variants(self, **kwargs):
        return self._variants.query_variants(**kwargs)

    def get_column_labels(self):
        return ['']

    def get_legend(self, *args, **kwargs):
        return []


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
            kwargs['regions'] = map(Region.from_str, kwargs['regions'])

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
            sexes = [token(sex) for sex in sexes]
            kwargs['sexes'] = or_node(sexes)

        if 'variant_type' in kwargs:
            variant_types = kwargs['variant_type']
            variant_types = [token(t) for t in variant_types]
            kwargs['variant_type'] = or_node(variant_types)

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
        min_value = float('-inf')
        max_value = float('inf')

        if 'minAltFrequencyPercent' in kwargs:
            if kwargs['minAltFrequencyPercent'] is not None:
                min_value = kwargs['minAltFrequencyPercent']
            kwargs.pop('minAltFrequencyPercent')

        if 'maxAltFrequencyPercent' in kwargs:
            if kwargs['maxAltFrequencyPercent'] is not None:
                max_value = kwargs['maxAltFrequencyPercent']
            kwargs.pop('maxAltFrequencyPercent')

        value_range = (min_value, max_value)

        value = 'all.altFreq'
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
                new_roles = and_node([
                    token(Role.prb.name),
                    not_node(token(Role.sib.name))
                ])

            if filter_option == 'unaffected only':
                new_roles = and_node([
                    not_node(token(Role.prb.name)),
                    token(Role.sib.name)
                ])

            if filter_option == 'affected and unaffected':
                new_roles = and_node([
                    token(Role.prb.name),
                    token(Role.sib.name)
                ])

            if filter_option == 'neither':
                new_roles = and_node([
                    not_node(token(Role.prb.name)),
                    not_node(token(Role.sib.name))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInChild')

        if not roles_query:
            return

        roles_query = or_node(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.parse(original_roles)
            kwargs['roles'] = and_node([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query

    def _transform_present_in_parent(self, kwargs):
        roles_query = []

        for filter_option in kwargs['presentInParent']:
            new_roles = None

            if filter_option == 'mother only':
                new_roles = and_node([
                    not_node(token(Role.dad.name)),
                    token(Role.mom.name)
                ])

            if filter_option == 'father only':
                new_roles = and_node([
                    token(Role.dad.name),
                    not_node(token(Role.mom.name))
                ])

            if filter_option == 'mother and father':
                new_roles = and_node([
                    token(Role.dad.name),
                    token(Role.mom.name)
                ])

            if filter_option == 'neither':
                new_roles = and_node([
                    not_node(token(Role.dad.name)),
                    not_node(token(Role.mom.name))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInParent')

        if not roles_query:
            return

        roles_query = or_node(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.parse(original_roles)
            kwargs['roles'] = and_node([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query
