'''
Created on Feb 29, 2016

@author: lubo
'''
from families.families_precompute import FamiliesPrecompute
import precompute
from families.merge_query import family_query_merge


def prepare_race(race):
    if isinstance(race, list):
        race = ','.join(race)
    race = race.lower()
    if race not in FamiliesPrecompute.get_races():
        return None
    return race


def prepare_family_race_query(data):
    if 'familyRace' not in data:
        return data

    family_race = prepare_race(data['familyRace'])
    del data['familyRace']

    if family_race is None:
        return data

    families_precompute = precompute.register.get('families_precompute')
    family_ids = families_precompute.race(family_race)

    data = family_query_merge(data, family_ids)
    return data
