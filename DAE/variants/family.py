'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np


class Person(object):

    def __init__(self, atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {}
        assert 'personId' in atts
        self.person_id = atts['personId']
        self.sex = atts['sex']
        self.role = atts['role']
        self.status = atts['status']

    def __repr__(self):
        return "Person({}; {}; {})".format(
            self.personId, self.role, self.gender)


class Family(object):

    def _build_trios(self, persons):
        trios = {}
        for pid, p in persons.items():
            if p['momId'] in persons and p['dadId'] in persons:
                pp = [pid]
                pp.append(p['momId'])
                pp.append(p['dadId'])
                trios[pid] = pp
        return trios

    def _build_persons(self, ped_df):
        persons = {}
        members = []
        for index, person in enumerate(ped_df.to_dict(orient="records")):
            person['index'] = index
            persons[person['personId']] = person
            members.append(Person(person))
        return persons, members

    def __init__(self, family_id, ped_df):
        self.family_id = family_id
        self.ped_df = ped_df
        assert np.all(ped_df['familyId'].isin(set([family_id])).values)
        self.persons, self.members = self._build_persons(self.ped_df)
        self.trios = self._build_trios(self.persons)

    def __len__(self):
        return len(self.ped_df)

    def members_index(self, person_ids):
        index = []
        for pid in person_ids:
            index.append(self.persons[pid]['index'])
        return index

    @property
    def members_in_order(self):
        return self.ped_df['personId'].values

    def members_in_roles(self, role_query):
        roles_df = self.ped_df[
            np.bitwise_and(
                self.ped_df.role.values,
                role_query.value
            ).astype(bool)
        ]
        if len(roles_df) == 0:
            return []
        return roles_df['personId'].values


class Families(object):

    def __init__(self, ped_df=None):
        self.ped_df = ped_df
        self.families = {}
        self.persons = {}

    def families_build(self, ped_df, family_class=Family):
        self.ped_df = ped_df
        for family_id, fam_df in self.ped_df.groupby(by='familyId'):
            family = family_class(family_id, fam_df)
            self.families[family_id] = family
            for person_id in self.ped_df['personId'].values:
                self.persons[person_id] = family

    def families_query_by_person(self, person_ids):
        res = {}
        for person_id in person_ids:
            fam = self.persons[person_id]
            if fam.family_id not in res:
                res[fam.family_id] = fam
        return res
