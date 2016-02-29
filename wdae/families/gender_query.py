'''
Created on Feb 29, 2016

@author: lubo
'''
import precompute
from families.merge_query import family_query_merge


def prepare_gender(gender):
    if isinstance(gender, list):
        gender = ','.join(gender)
    if gender.lower() == 'male':
        return 'M'
    if gender.lower() == 'female':
        return 'F'
    return None


def prepare_family_sib_gender_query(data):
    if 'familySibGender' not in data:
        return data

    family_sib_gender = prepare_gender(data['familySibGender'])
    del data['familySibGender']

    if family_sib_gender is None:
        return data

    families_precompute = precompute.register.get('families_precompute')
    family_ids = families_precompute.siblings(family_sib_gender)

    data = family_query_merge(data, family_ids)
    return data


def prepare_family_prb_gender_query(data):
    if 'familyPrbGender' not in data:
        return data

    family_prb_gender = prepare_gender(data['familyPrbGender'])
    del data['familyPrbGender']

    if family_prb_gender is None:
        return data

    families_precompute = precompute.register.get('families_precompute')
    family_ids = families_precompute.probands(family_prb_gender)

    data = family_query_merge(data, family_ids)
    return data
