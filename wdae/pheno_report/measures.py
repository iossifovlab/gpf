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
from helpers.pvalue import format_pvalue, colormap_pvalue


class Measures(Preload):

    @staticmethod
    def _float_conv(val):
        if val == "NaN":
            return val
        else:
            return float(val)

    def load_instruments(self):
        instruments = self.phdb.instruments
        res = []
        for name, instrument in instruments.items():
            if instrument.name == 'pheno_common':
                continue
            df = self.phdb.get_measures_df(instrument.name, stats='continuous')
            if np.any(df.has_probands):
                res.append(name)
        return sorted(res)

    def _build_measure_description(self, row):
        def violin_plot(measure_id, small=None):
            if small is None:
                return '{}.violinplot.png'.format(measure_id)
            else:
                return '{}.violinplot_small.png'.format(measure_id)

        def histogram_plot(measure_id, small=None):
            if small is None:
                return '{}.prb_distribution.png'.format(measure_id)
            else:
                return '{}.prb_distribution_small.png'.format(measure_id)

        def corr_nviq_plot(measure_id, small=None):
            if small is None:
                return '{}.prb_regression_by_nviq.png'.format(measure_id)
            else:
                return '{}.prb_regression_by_nviq_small.png'.format(measure_id)

        def corr_age_plot(measure_id, small=None):
            if small is None:
                return '{}.prb_regression_by_age.png'.format(measure_id)
            else:
                return '{}.prb_regression_by_age_small.png'.format(measure_id)

        measure_id = row['measure_id']
        desc = {'measure': measure_id,
                'instrument': row['instrument_name'],
                'measure_name': row['measure_name'],
                'desc': None,  # v.description.decode('utf-8'),
                'min': row['min_value'],
                'max': row['max_value'],
                'violin_plot': violin_plot(measure_id),
                'violin_plot_small': violin_plot(measure_id, 'small'),
                'hist': histogram_plot(measure_id),
                'hist_small': histogram_plot(measure_id, 'small'),
                'corr_nviq': corr_nviq_plot(measure_id),
                'corr_nviq_small': corr_nviq_plot(measure_id, 'small'),
                'corr_age': corr_age_plot(measure_id),
                'corr_age_small': corr_age_plot(measure_id, 'small')}
        return desc

    def _build_measure_stats_description(self, desc, row):

        desc['nviq_male_pval'] = format_pvalue(
            row['pvalue.prb.M.pheno_common.non_verbal_iq'])
        desc['nviq_male_pval_bg'] = colormap_pvalue(
            row['pvalue.prb.M.pheno_common.non_verbal_iq'])
        desc['nviq_female_pval'] = format_pvalue(
            row['pvalue.prb.F.pheno_common.non_verbal_iq'])
        desc['nviq_female_pval_bg'] = colormap_pvalue(
            row['pvalue.prb.F.pheno_common.non_verbal_iq'])
        desc['age_male_pval'] = format_pvalue(
            row['pvalue.prb.M.pheno_common.age'])
        desc['age_male_pval_bg'] = colormap_pvalue(
            row['pvalue.prb.M.pheno_common.age'])
        desc['age_female_pval'] = format_pvalue(
            row['pvalue.prb.F.pheno_common.age'])
        desc['age_female_pval_bg'] = colormap_pvalue(
            row['pvalue.prb.F.pheno_common.age'])

    def load_desc(self, instrument=None):

        d = {}
        res = []
        if instrument == 'pheno_common':
            return res

        measures = self.phdb.get_measures_df(
            instrument=instrument,
            stats='continuous'
        )
        for _index, row in measures.iterrows():
            # print("loading measure: {}".format(row['measure_id']))
            if not row['has_probands']:
                continue
            desc = self._build_measure_description(row)
            res.append(desc)
            d[desc['measure']] = desc

        if not res:
            return res

        corr_df = self.phdb.get_measures_corellations_df(
            measures,
            ['pheno_common.non_verbal_iq', 'pheno_common.age'],
            'prb')

        for _index, row in corr_df.iterrows():
            measure_id = row['measure_id']
            if measure_id not in d:
                continue
            desc = d[measure_id]
            self._build_measure_stats_description(desc, row)

        return res

    def load_list(self):
        d = []
        measures = self.phdb.get_measures_df(
            # instrument='ssc_commonly_used',
            stats='continuous'
        )
        print(measures.head())
        for _index, row in measures.iterrows():
            if 'pheno_common' in row['measure_id']:
                continue
            d.append({
                'measure': row['measure_id'],
                'min': row['min_value'],
                'max': row['max_value'],
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

    def get_values_df(self, measure_id):
        return self.phdb.get_values_df([measure_id], role='prb')

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
