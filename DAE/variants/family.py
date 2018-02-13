'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np


class Family(object):

    @staticmethod
    def samples_to_alleles(samples):
        return np.stack([2 * samples, 2 * samples + 1]). \
            reshape([1, 2 * len(samples)], order='F')[0]

    def __init__(self, family_id, ped_df):
        self.family_id = family_id
        self.ped_df = ped_df
        assert np.all(ped_df['familyId'].isin(set([family_id])).values)
        self.samples = self.ped_df.index.values
        self.alleles = self.samples_to_alleles(self.samples)

    def psamples(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ].index.values

    def palleles(self, person_ids):
        p = self.psamples(person_ids)
        return self.samples_to_alleles(p)


class Families(object):

    def __init__(self, ped_df=None):
        self.ped_df = ped_df
        self.families = {}
        self.persons = {}

    def families_build(self, ped_df):
        self.ped_df = ped_df
        for family_id, fam_df in self.ped_df.groupby(by='familyId'):
            family = Family(family_id, fam_df)
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
