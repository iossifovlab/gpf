from __future__ import print_function
import itertools

from RegionOperations import Region
from variants.attributes import Role, AQuery, RoleQuery, QLeaf, QAnd, QNot, \
    SexQuery, Sex, VariantTypeQuery, VariantType
import logging
# from datasets.helpers import transform_variants_to_lists

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
            # FIXME: this should be handled by AQuery..
            sexes = [Sex.from_name(sex) for sex in sexes]
            kwargs['sexes'] = SexQuery.any_of(*sexes)

        if 'variant_type' in kwargs:
            variant_types = kwargs['variant_type']
            variant_types = [VariantType.from_name(t) for t in variant_types]
            variant_types = VariantTypeQuery.any_of(*variant_types)
            kwargs['variant_type'] = variant_types

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
        print(value_range)

        value = 'all.altFreq'
        if 'real_attr_filter' not in kwargs:
            kwargs['real_attr_filter'] = {}

        if value not in kwargs['real_attr_filter']:
            kwargs['real_attr_filter'][value] = []

        kwargs['real_attr_filter'][value].append(value_range)

    def _transform_present_in_child(self, kwargs):
        roles_query = None

        for filter_option in kwargs['presentInChild']:
            new_roles = None

            if filter_option == 'affected only':
                new_roles = AQuery.any_of(Role.prb) \
                    .and_not_(AQuery.any_of(Role.sib))

            if filter_option == 'unaffected only':
                new_roles = AQuery.any_of(Role.sib) \
                    .and_not_(AQuery.any_of(Role.prb))

            if filter_option == 'affected and unaffected':
                new_roles = AQuery.all_of(Role.prb, Role.sib)

            if filter_option == 'neither':
                new_roles = AQuery.any_of(Role.prb).not_() \
                    .and_not_(AQuery.any_of(Role.sib))

            if new_roles:
                if not roles_query:
                    roles_query = new_roles
                else:
                    roles_query.or_(new_roles)

        if roles_query:
            original_roles = kwargs.get('roles', None)
            if original_roles is not None:
                original_roles_query = RoleQuery.parse(original_roles)
                kwargs['roles'] = original_roles_query.and_(roles_query)
            else:
                kwargs['roles'] = roles_query

        kwargs.pop('presentInChild')

    def _transform_present_in_parent(self, kwargs):
        roles_query = None

        for filter_option in kwargs['presentInParent']:
            new_roles = None

            if filter_option == 'mother only':
                new_roles = AQuery.any_of(Role.mom) \
                    .and_not_(AQuery.any_of(Role.dad))

            if filter_option == 'father only':
                new_roles = AQuery.any_of(Role.dad) \
                    .and_not_(AQuery.any_of(Role.mom))

            if filter_option == 'mother and father':
                new_roles = AQuery.all_of(Role.dad, Role.mom)

            if filter_option == 'neither':
                new_roles = AQuery.any_of(Role.dad).not_() \
                    .and_not_(AQuery.any_of(Role.mom))

            if new_roles:
                if not roles_query:
                    roles_query = new_roles
                else:
                    roles_query.or_(new_roles)

        if roles_query:
            original_roles = kwargs.get('roles', None)
            if original_roles is not None:
                original_roles_query = RoleQuery.parse(original_roles)
                kwargs['roles'] = original_roles_query.and_(roles_query)
            else:
                kwargs['roles'] = roles_query

        kwargs.pop('presentInParent')
