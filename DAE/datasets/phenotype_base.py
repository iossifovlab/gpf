'''
Created on Mar 2, 2017

@author: lubo
'''
import numpy as np


class PhenotypeQueryMixin(object):

    def _select_continous_measure_df(self, measure_id, mmin, mmax, roles=None):
        df = self.pheno_db.get_persons_values_df([measure_id], roles=roles)
        df.dropna(inplace=True)

        mvals = df[measure_id]
        selected = None
        if mmin is not None and mmax is not None:
            selected = df[np.logical_and(mvals >= mmin, mvals <= mmax)]
        elif mmin is not None:
            selected = df[mvals >= mmin]
        elif mmax is not None:
            selected = df[mvals <= mmax]
        else:
            selected = df
        return selected

    def get_families_by_measure_continuous(
            self, measure_id, mmin=None, mmax=None, roles=None):
        assert self.pheno_db is not None

        selected = self._select_continous_measure_df(
            measure_id, mmin, mmax, roles=roles)
        return set(selected.family_id.values)

    def get_persons_by_measure_continuous(
            self, measure_id, mmin=None, mmax=None, roles=None):
        assert self.pheno_db is not None

        selected = self._select_continous_measure_df(
            measure_id, mmin, mmax, roles=roles)
        return set(selected.person_id.values)

    def _select_categorical_measure_df(
            self, measure_id, selection, roles=None):

        domain = self.get_measure_domain_categorical(measure_id)
        selection = set(selection)
        assert selection <= domain

        df = self.pheno_db.get_persons_values_df([measure_id], roles=roles)
        df.dropna(inplace=True)

        selected = df[df[measure_id].isin(selection)]
        return selected

    def get_families_by_measure_categorical(
            self, measure_id, selection, roles=None):
        assert self.pheno_db is not None

        selected = self._select_categorical_measure_df(
            measure_id, selection=selection, roles=roles)
        return set(selected.family_id.values)

    def get_measure_domain_categorical(self, measure_id):
        assert self.pheno_db is not None

        m = self.pheno_db.get_measure(measure_id)
        assert m.measure_type == 'categorical'
        return set(m.value_domain.split(','))
