'''
Created on Feb 29, 2016

@author: lubo
'''
from families.families_precompute import FamiliesPrecompute
import precompute
from families.merge_query import merge_family_ids


def prepare_race(race):
    if isinstance(race, list):
        race = ','.join(race)
    race = race.lower()
    if race not in FamiliesPrecompute.get_races():
        return None
    return race


def prepare_family_race_query(data, family_ids=None):
    if 'familyRace' not in data:
        return family_ids

    family_race = prepare_race(data['familyRace'])
    del data['familyRace']

    if family_race is None:
        return family_ids

    families_precompute = precompute.register.get('families_precompute')
    result = families_precompute.race(family_race)
    return merge_family_ids(result, family_ids)
