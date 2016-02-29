'''
Created on Feb 29, 2016

@author: lubo
'''
import precompute
from families.merge_query import family_query_merge


def prepare_trio_quad(trio_quad):
    if isinstance(trio_quad, list):
        trio_quad = ','.join(trio_quad)
    if trio_quad.lower() == 'trio':
        return 'trio'
    if trio_quad.lower() == 'quad':
        return 'quad'
    return None


def prepare_family_trio_quad_query(data):
    if 'familyQuadTrio' not in data:
        return data

    family_trio_quad = prepare_trio_quad(data['familyQuadTrio'])
    del data['familyQuadTrio']

    if family_trio_quad is None:
        return data

    families_precompute = precompute.register.get('families_precompute')

    if family_trio_quad == 'trio':
        family_ids = families_precompute.trios()
    elif family_trio_quad == 'quad':
        family_ids = families_precompute.quads()
    else:
        raise ValueError()
    data = family_query_merge(data, family_ids)
    return data
