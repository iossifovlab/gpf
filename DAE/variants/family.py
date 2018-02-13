'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np


class Family(object):

    def __init__(self, family_id, ped_df):
        self.family_id = family_id
        self.ped_df = ped_df
        assert np.all(ped_df['familyId'].isin(set([family_id])).values)
        self.samples = self.ped_df.index.values
        self.allels = np.stack([2 * self.samples, 2 * self.samples + 1]). \
            reshape([1, 2 * len(self.samples)], order='F')[0]

    def psamples(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ].index.values

    def pallels(self, person_ids):
        p = self.psamples(person_ids)
        return np.stack([2 * p, 2 * p + 1]). \
            reshape([1, 2 * len(p)], order='F')[0]


class Families(object):

    def __init__(self, ped_df):
        self.ped_df = ped_df
