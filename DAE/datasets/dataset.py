from __future__ import print_function
import itertools

from RegionOperations import Region
from variants.attributes import Role, AQuery, RoleQuery, QLeaf, QAnd, QNot


class Dataset(object):

    def __init__(self, name, variants):
        self.name = name
        self._variants = variants

    def get_variants(self, **kwargs):
        return self._variants.query_variants(**kwargs)


class DatasetWrapper(Dataset):

    def __init__(self, *args, **kwargs):
        super(DatasetWrapper, self).__init__(*args, **kwargs)

    FILTER_RENAMES_MAP = {
        'familyIds': 'family_ids',
        'gender': 'sexes',
        'variantTypes': 'variant_type',
        'effectTypes': 'effect_types',
        'regionS': 'regions',
    }

    # inChild
    ##### presentInChild
    ##### presentInParent
    # genomicScores
    # geneSyms
    ##### limit
    # callSet
    # minParentsCalled
    # maxAltFreqPrcnt
    # minAltFreqPrcnt
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

        return itertools.islice(
            super(DatasetWrapper, self).get_variants(**kwargs), limit)

    def _transform_present_in_child(self, kwargs):
        print("kwargs", kwargs)
        roles_query = None

        for filter_option in kwargs['presentInChild']:
            new_roles = None

            if filter_option == 'affected only':
                new_roles = AQuery.any_of(Role.prb).and_not_(AQuery.any_of(Role.sib))

            if filter_option == 'unaffected only':
                new_roles = AQuery.any_of(Role.sib).and_not_(AQuery.any_of(Role.prb))

            if filter_option == 'affected and unaffected':
                new_roles = AQuery.all_of(Role.prb, Role.sib)

            if filter_option == 'neither':
                new_roles = AQuery.any_of(Role.prb).not_().and_not_(AQuery.any_of(Role.sib))

            if new_roles:
                if not roles_query:
                    roles_query = new_roles
                else:
                    roles_query.or_(new_roles)

        if roles_query:
            original_roles = kwargs.get('roles', None)
            if original_roles is not None:
                print("original_roles is not none")
                original_roles_query = RoleQuery.parse(original_roles)
                print(original_roles_query)
                kwargs['roles'] = original_roles_query.and_(roles_query)
            else:
                kwargs['roles'] = roles_query

    def _transform_present_in_parent(self, kwargs):
        pass
