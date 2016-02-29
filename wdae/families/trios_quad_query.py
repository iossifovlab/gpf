'''
Created on Feb 29, 2016

@author: lubo
'''
import precompute
from families.merge_query import merge_family_ids


def prepare_trio_quad(trio_quad):
    if isinstance(trio_quad, list):
        trio_quad = ','.join(trio_quad)
    if trio_quad.lower() == 'trio':
        return 'trio'
    if trio_quad.lower() == 'quad':
        return 'quad'
    return None


def prepare_family_trio_quad_query(data, family_ids=None):
    assert family_ids is None or isinstance(family_ids, set)

    if 'familyQuadTrio' not in data:
        return family_ids

    family_trio_quad = prepare_trio_quad(data['familyQuadTrio'])
    del data['familyQuadTrio']

    if family_trio_quad is None:
        return family_ids

    families_precompute = precompute.register.get('families_precompute')

    if family_trio_quad == 'trio':
        result = families_precompute.trios()
    elif family_trio_quad == 'quad':
        result = families_precompute.quads()
    else:
        raise ValueError()

    return merge_family_ids(result, family_ids)
