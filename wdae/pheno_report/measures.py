'''
Created on Nov 16, 2015

@author: lubo
'''
# import os
# import csv
import numpy as np
# from django.conf import settings
import pandas as pd
import statsmodels.formula.api as sm
from preloaded.register import Preload
# from helpers.pvalue import colormap_value
import precompute
import itertools
from pheno.pheno_db import PhenoDB


class Measures(Preload):

    @staticmethod
    def _float_conv(val):
        if val == "NaN":
            return val
        else:
            return float(val)

    def load_instruments(self):
        instruments = self.phdb.instruments
        res = [i.name for i in instruments.values()]
        return res

    def load_desc(self, instrument=None):
        d = []
        measures = self.phdb.get_measures_df(
            instrument=instrument,
            stats='continuous'
        )
        for _index, row in measures.iterrows():
            # print("loading measure: {}".format(row['measure_id']))
            d.append({
                'measure': row['measure_id'],
                'instrument': row['instrument_name'],
                'measure_name': row['measure_name'],
                'desc': None,  # v.description.decode('utf-8'),
                'min': row['min_value'],
                'max': row['max_value'],
            })
        return d

    def load_list(self):
        d = []
        measures = self.phdb.get_measures_df(
            # instrument='ssc_commonly_used',
            stats='continuous'
        )
        for _index, row in measures.iterrows():
            d.append({
                'measure': row['measure_id'],
            })
        return d

    def __init__(self):
        pass

    def load(self):
        self.phdb = PhenoDB()
        self.phdb.load()

        self.families_precompute = precompute.register.get(
            'pheno_families_precompute')

        self.probands_gender = \
            zip(itertools.cycle(['M']),
                self.families_precompute.probands('M'))
        self.probands_gender.extend(
            zip(itertools.cycle(['F']),
                self.families_precompute.probands('F')))

    def get(self):
        return self

    def has_measure(self, measure_id):
        return self.phdb.has_measure(measure_id)

#     @staticmethod
#     def split_measure_id(measure_id):
#         assert '.' in measure_id
#         [instrument_name, measure_name] = measure_id.split('.')
#         return (instrument_name, measure_name)

    def get_measure_df(self, measure_id):
        if not self.has_measure(measure_id):
            raise ValueError("unsupported phenotype measure")

        persons_df = self.phdb.get_persons_df(role='prb')

        value_df = self.phdb.get_values_df(
            ['pheno_common.age', 'pheno_common.non_verbal_iq', measure_id],
            role='prb')

        df = persons_df.join(
            value_df.set_index('person_id'), on='person_id', rsuffix='_val')
        res_df = df.dropna()

        return res_df

    def _select_measure_df(self, measure_id, mmin, mmax):
        df = self.get_measure_df(measure_id)
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

    def get_measure_families(self, measure, mmin=None, mmax=None):
        selected = self._select_measure_df(measure, mmin, mmax)
        return selected['family_id'].values

    def get_measure_probands(self, measure, mmin=None, mmax=None):
        selected = self._select_measure_df(measure, mmin, mmax)
        return selected['person_id'].values


class NormalizedMeasure(object):

    def __init__(self, measure_id):

        from preloaded.register import get_register
        self.measure_id = measure_id
        register = get_register()
        measures = register.get('pheno_measures')

        if not measures.has_measure(measure_id):
            raise ValueError(
                "unknown phenotype measure: {}".format(measure_id))

        self.df = measures.get_measure_df(measure_id)
        self.by = []

    def _rename_forward(self, df, mapping):
        names = df.columns.tolist()
        for n, f in mapping:
            if n in names:
                names[names.index(n)] = f
        df.columns = names

    def _rename_backward(self, df, mapping):
        names = df.columns.tolist()
        for n, f in mapping:
            if f in names:
                names[names.index(f)] = n
        df.columns = names

    def normalize(self, by=[]):
        assert isinstance(by, list)
        assert all(map(lambda b: b in [
            'pheno_common.age', 'pheno_common.non_verbal_iq'], by))
        self.by = by

        if not by:
            dn = pd.Series(
                index=self.df.index, data=self.df[self.measure_id].values)
            self.df['normalized'] = dn
            self.formula = self.measure_id

        else:
            self.formula = '{} ~ {}'.format(self.measure_id, ' + '.join(by))

            variables = [
                (b, 'X_{}'.format(i)) if b != self.measure_id else (b, 'R')
                for (i, b) in enumerate(by)]
            mapping = [(self.measure_id, 'R')]
            mapping.extend(variables)
            formula = "R ~ {}".format(
                ' + '.join([f for (_n, f) in variables]))

            self._rename_forward(self.df, mapping)
            model = sm.ols(formula=formula,
                           data=self.df)
            fitted = model.fit()
            self._rename_backward(self.df, mapping)

            dn = pd.Series(index=self.df.index, data=fitted.resid)
            self.df['normalized'] = dn
            return self.df
