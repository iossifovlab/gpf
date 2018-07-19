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
        self.family_id = atts['familyId']
        self.family_index = atts['familyIndex']
        self.person_id = atts['personId']
        self.person_index = atts['personIndex']
        self.sample_id = atts['sampleId']
        self.index = atts['index']
        self.sex = atts['sex']
        self.role = atts['role']
        self.status = atts['status']
        self.mom = atts['momId']
        self.dad = atts['dadId']

    def __repr__(self):
        return "Person({} ({}); {}; {})".format(
            self.person_id, self.family_id, self.role, self.sex)

    def has_mom(self):
        return not (self.mom is None or self.mom == '0')

    def has_dad(self):
        return not (self.dad is None or self.dad == '0')

    def has_parent(self):
        return self.has_dad() or self.has_mom()

    def get_attr(self, item):
        return self.atts.get(item)


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
        self.family_index = ped_df['familyIndex'].values[0]
        assert np.all(ped_df['familyIndex'] == self.family_index)

        self.persons, self.members_in_order = self._build_persons(self.ped_df)
        self.trios = self._build_trios(self.persons)

    def __len__(self):
        return len(self.ped_df)

    def members_index(self, person_ids):
        index = []
        for pid in person_ids:
            index.append(self.persons[pid]['index'])
        return index

    @property
    def members_ids(self):
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


class FamiliesBase(object):

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

    def persons_without_parents(self):
        person = []
        for fam in self.families.values():
            for p in fam.members_in_order:
                if not p.has_parent():
                    person.append(p)
        return person

    def persons_index(self, persons):
        return sorted([p.index for p in persons])
