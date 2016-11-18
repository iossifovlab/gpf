'''
Created on Nov 15, 2016

@author: lubo
'''
import numpy as np


class FamilyFilters(object):

    def __init__(self, phdb):
        self.phdb = phdb

    def _select_measure_df(self, measure_id, mmin, mmax):
        df = self.phdb.get_measure_values_df(measure_id, roles=['prb'])
        m = df[measure_id]
        selected = None
        if mmin is not None and mmax is not None:
            selected = df[np.logical_and(m >= mmin, m <= mmax)]
        elif mmin is not None:
            selected = df[m >= mmin]
        elif mmax is not None:
            selected = df[m <= mmax]
        else:
            selected = df
        return selected

    def get_measure_families(self, measure_id, mmin=None, mmax=None):
        selected = self._select_measure_df(measure_id, mmin, mmax)
        return set([pid.split('.')[0] for pid in selected['person_id'].values])

    def get_measure_probands(self, measure_id, mmin=None, mmax=None):
        selected = self._select_measure_df(measure_id, mmin, mmax)
        return selected['person_id'].values
