'''
Created on Apr 10, 2017

@author: lubo
'''
from __future__ import print_function

import os
import traceback
import matplotlib as mpl
import numpy as np

from pheno.pheno_db import Measure
mpl.use('PS')
import matplotlib.pyplot as plt  # @IgnorePep8
plt.ioff()

from pheno_browser.db import DbManager  # @IgnorePep8
from pheno.common import Role, MeasureType  # @IgnorePep8

from pheno_browser.graphs import draw_linregres  # @IgnorePep8
from pheno_browser.graphs import draw_measure_violinplot  # @IgnorePep8
from pheno_browser.graphs import draw_categorical_violin_distribution  # @IgnorePep8
from pheno_browser.graphs import draw_ordinal_violin_distribution  # @IgnorePep8
from common.progress import progress, progress_nl  # @IgnorePep8


class PreparePhenoBrowserBase(object):

    LARGE_DPI = 150
    SMALL_DPI = 16

    def __init__(self, pheno_name, pheno_db, pheno_regression, output_dir):
        assert os.path.exists(output_dir)
        self.output_dir = output_dir
        self.output_base = os.path.basename(output_dir)
        self.pheno_db = pheno_db
        self.pheno_regressiong = pheno_regression

        self.browser_db = os.path.join(
            output_dir,
            "{}_browser.db".format(pheno_name)
        )

    def load_measure(self, measure):
        df = self.pheno_db.get_persons_values_df([measure.measure_id])
        return df

    def _augment_measure_values_df(self, augment, augment_name, measure):
        assert augment is not None
        assert isinstance(augment, Measure)

        augment_instrument = augment.instrument_name
        augment_measure = augment.measure_name

        if augment_instrument is not None:
            augment_id = '{}.{}'.format(
                augment_instrument, augment_measure)
        else:
            augment_id = '{}.{}'.format(
                measure.instrument_name, augment_measure)

        if augment_id == measure.measure_id:
            return None
        if not self.pheno_db.has_measure(augment_id):
            return None

        df = self.pheno_db.get_persons_values_df(
            [augment_id, measure.measure_id])
        df.loc[df.role == Role.mom, 'role'] = Role.parent
        df.loc[df.role == Role.dad, 'role'] = Role.parent

        df.rename(columns={augment_id: augment_name}, inplace=True)
        return df

    @staticmethod
    def _measure_to_dict(measure):
        return {
            'measure_id': measure.measure_id,
            'instrument_name': measure.instrument_name,
            'measure_name': measure.measure_name,
            'measure_type': measure.measure_type,
            'values_domain': measure.values_domain
        }

    def load_measure_and_age(self, measure):
        age_id = self.pheno_regressiong.get_age_measure_id(measure.measure_id)
        if not age_id:
            return None
        age = self.pheno_db.get_measure(age_id)
        return self._augment_measure_values_df(age, 'age', measure)

    def load_measure_and_nonverbal_iq(self, measure):
        nonverbal_iq_id = self.pheno_regressiong.get_nonverbal_iq_measure_id(
            measure.measure_id)
        if not nonverbal_iq_id:
            return None
        nonverbal_iq = self.pheno_db.get_measure(nonverbal_iq_id)
        return self._augment_measure_values_df(
            nonverbal_iq, 'nonverbal_iq', measure)

    def figure_filepath(self, measure, suffix):
        filename = "{}.{}.png".format(measure.measure_id, suffix)
        outdir = os.path.join(self.output_dir, measure.instrument_name)
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        filepath = os.path.join(outdir, filename)
        return filepath

    def figure_path(self, measure, suffix):
        filename = "{}.{}.png".format(measure.measure_id, suffix)
        outdir = os.path.join(self.output_base, measure.instrument_name)

        filepath = os.path.join(outdir, filename)
        return filepath

    def save_fig(self, measure, suffix):
        if '/' in measure.measure_id:
            return (None, None)

        small_filepath = self.figure_filepath(
            measure, "{}_small".format(suffix))
        plt.savefig(small_filepath, dpi=self.SMALL_DPI)

        filepath = self.figure_filepath(measure, suffix)
        plt.savefig(filepath, dpi=self.LARGE_DPI)
        plt.close()
        return (
            self.figure_path(
                measure, "{}_small".format(suffix)),
            self.figure_path(
                measure, suffix)
        )

    def build_regression_by_age(self, measure):
        res = {}
        age_id = self.pheno_regressiong.get_age_measure_id(measure.measure_id)
        if age_id is None:
            return res
        if measure.measure_id == age_id:
            return res

        df = self.load_measure_and_age(measure)
        if df is None:
            return res
        dd = df[df.role == Role.prb]
        dd.loc[:, 'age'] = dd['age'].astype(np.float32)
        dd = dd[np.isfinite(dd.age)]

        if dd[measure.measure_id].nunique() == 1:
            return res

        if len(dd) <= 5:
            return res

        res_male, res_female = draw_linregres(
            dd, 'age', measure.measure_id, jitter=0.1)
        res['pvalue_correlation_age_male'] = res_male.pvalues['age'] \
            if res_male is not None else None
        res['pvalue_correlation_age_female'] = res_female.pvalues['age'] \
            if res_female is not None else None

        if res_male is not None or res_female is not None:
            (res['figure_correlation_age_small'],
             res['figure_correlation_age']) = \
                self.save_fig(measure, "prb_regression_by_age")
        return res

    def build_regression_by_nviq(self, measure):
        res = {}
        nviq_id = self.pheno_regressiong \
            .get_nonverbal_iq_measure_id(measure.measure_id)
        if nviq_id is None:
            return res
        if measure.measure_id == nviq_id:
            return res
        age_id = self.pheno_regressiong.get_age_measure_id(measure.measure_id)
        if measure.measure_id == age_id:
            return res

        df = self.load_measure_and_nonverbal_iq(measure)
        if df is None:
            return res

        dd = df[df.role == Role.prb]
        dd.loc[:, 'nonverbal_iq'] = dd['nonverbal_iq'].astype(np.float32)
        dd = dd[np.isfinite(dd.nonverbal_iq)]

        if len(dd) <= 5:
            return res

        if dd[measure.measure_id].nunique() == 1:
            return res

        res_male, res_female = draw_linregres(
            dd, 'nonverbal_iq', measure.measure_id, jitter=0.1)

        res['pvalue_correlation_nviq_male'] = \
            res_male.pvalues['nonverbal_iq'] \
            if res_male is not None else None
        res['pvalue_correlation_nviq_female'] = \
            res_female.pvalues['nonverbal_iq'] \
            if res_female is not None else None

        if res_male is not None or res_female is not None:
            (res['figure_correlation_nviq_small'],
             res['figure_correlation_nviq']) = self.save_fig(
                 measure, "prb_regression_by_nviq")
        return res

    def build_values_violinplot(self, measure):
        df = self.load_measure(measure)
        drawn = draw_measure_violinplot(df, measure.measure_id)

        res = {}

        if drawn:
            (res['figure_distribution_small'],
             res['figure_distribution']) = self.save_fig(measure, "violinplot")

        return res

    def build_values_categorical_distribution(self, measure):
        df = self.load_measure(measure)
        drawn = draw_categorical_violin_distribution(df, measure.measure_id)

        res = {}
        if drawn:
            (res['figure_distribution_small'],
             res['figure_distribution']) = \
                self.save_fig(measure, "distribution")

        return res

    def build_values_other_distribution(self, measure):
        df = self.load_measure(measure)
        drawn = draw_categorical_violin_distribution(df, measure.measure_id)

        res = {}
        if drawn:
            (res['figure_distribution_small'],
             res['figure_distribution']) = \
                self.save_fig(measure, "distribution")

        return res

    def build_values_ordinal_distribution(self, measure):
        df = self.load_measure(measure)
        drawn = draw_ordinal_violin_distribution(df, measure.measure_id)

        res = {}
        if drawn:
            (res['figure_distribution_small'],
             res['figure_distribution']) = \
                self.save_fig(measure, "distribution")

        return res

    def dump_browser_variable(self, var):
        print('-------------------------------------------')
        print(var['measure_id'])
        print('-------------------------------------------')
        print('instrument: {}'.format(var['instrument_name']))
        print('measure:    {}'.format(var['measure_name']))
        print('type:       {}'.format(var['measure_type']))
        print('domain:     {}'.format(var['values_domain']))
        print('-------------------------------------------')

    def handle_measure(self, measure):
        res = PreparePhenoBrowserBase._measure_to_dict(measure)

        if measure.measure_type == MeasureType.continuous:
            res.update(self.build_values_violinplot(measure))
            res.update(self.build_regression_by_nviq(measure))
            res.update(self.build_regression_by_age(measure))
        elif measure.measure_type == MeasureType.ordinal:
            res.update(self.build_values_ordinal_distribution(measure))
            res.update(self.build_regression_by_nviq(measure))
            res.update(self.build_regression_by_age(measure))
        elif measure.measure_type == MeasureType.categorical:
            res.update(self.build_values_categorical_distribution(measure))
        return res

    def run(self):
        db = DbManager(dbfile=self.browser_db)
        db.build()
        progress_nl()
        print("Instruments:", list(self.pheno_db.instruments.keys()))
        progress_nl()
        for instrument in self.pheno_db.instruments.values():
            progress_nl()
            progress(text=str(instrument) + "\n")
            progress_nl()
            for measure in instrument.measures.values():
                progress(text=str(measure) + "\n")
                try:
                    var = self.handle_measure(measure)
                    db.save(var)
                except Exception as ex:
                    print("--------------------------------------------------")
                    print(
                        "Exception while processing measure:", 
                        str(measure), ex)
                    traceback.print_exc()
                    print("--------------------------------------------------")
