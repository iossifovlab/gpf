'''
Created on Feb 29, 2016

@author: lubo
'''
import precompute
from families.merge_query import merge_family_ids


def prepare_gender(gender):
    if isinstance(gender, list):
        gender = ','.join(gender)
    if gender.lower() == 'male':
        return 'M'
    if gender.lower() == 'female':
        return 'F'
    return None


def prepare_family_sib_gender_query(data, family_ids=None):
    assert family_ids is None or isinstance(family_ids, set)

    if 'familySibGender' not in data:
        return family_ids

    family_sib_gender = prepare_gender(data['familySibGender'])
    del data['familySibGender']

    if family_sib_gender is None:
        return family_ids

    families_precompute = precompute.register.get('families_precompute')
    result = families_precompute.siblings(family_sib_gender)

    return merge_family_ids(result, family_ids)


def prepare_family_prb_gender_query(data, family_ids=None):
    assert family_ids is None or isinstance(family_ids, set)

    if 'familyPrbGender' not in data:
        return family_ids

    family_prb_gender = prepare_gender(data['familyPrbGender'])
    del data['familyPrbGender']

    if family_prb_gender is None:
        return family_ids

    families_precompute = precompute.register.get('families_precompute')
    result = families_precompute.probands(family_prb_gender)

    return merge_family_ids(result, family_ids)
