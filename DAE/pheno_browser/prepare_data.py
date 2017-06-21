'''
Created on Apr 10, 2017

@author: lubo
'''
import os
import matplotlib as mpl
mpl.use('PS')

import matplotlib.pyplot as plt
plt.ioff()

from DAE import pheno
from pheno_browser.graphs import draw_linregres, draw_measure_violinplot,\
    draw_categorical_violin_distribution,\
    draw_ordinal_violin_distribution
from pheno_browser.models import VariableBrowserModelManager,\
    VariableBrowserModel
from common.progress import progress, progress_nl


class PreparePhenoBrowserBase(object):

    LARGE_DPI = 300
    SMALL_DPI = 16

    def __init__(self, pheno_db, output_dir):
        assert os.path.exists(output_dir)
        self.output_dir = output_dir
        self.output_base = os.path.basename(output_dir)
        print(self.output_base)
        self.pheno_db = pheno.get_pheno_db(pheno_db)
        self.browser_db = os.path.join(
            output_dir,
            "{}_browser.db".format(pheno_db)
        )

    def load_measure(self, measure):
        df = self.pheno_db.get_persons_values_df([measure.measure_id])
        df.loc[df.role == 'mom', 'role'] = 'parent'
        df.loc[df.role == 'dad', 'role'] = 'parent'
        return df

    def _augment_measure_values_df(self, augment, measure):
        augment_instrument = augment['instrument_name']
        augment_measure = augment['measure_name']

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
        df.loc[df.role == 'mom', 'role'] = 'parent'
        df.loc[df.role == 'dad', 'role'] = 'parent'

        columns = list(df.columns)
        columns[columns.index(augment_id)] = augment['name']
        df.columns = columns
        return df

    def load_measure_and_age(self, measure):
        return self._augment_measure_values_df(
            self.pheno_db.age, measure)

    def load_measure_and_nonverbal_iq(self, measure):
        return self._augment_measure_values_df(
            self.pheno_db.nonverbal_iq, measure)

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

    def build_regression_by_age(self, measure, res):
        age_id = self.pheno_db.get_age_measure_id(measure.measure_id)
        if age_id is None:
            return None, None
        if measure.measure_id == age_id:
            return None, None

        df = self.load_measure_and_age(measure)
        if df is None:
            return None, None

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            res_male, res_female = draw_linregres(
                dd, 'age', measure.measure_id, jitter=0.1)
            res.pvalue_correlation_age_male = res_male.pvalues['age'] \
                if res_male is not None else None
            res.pvalue_correlation_age_female = res_female.pvalues['age'] \
                if res_female is not None else None

            (res.figure_correlation_age_small,
             res.figure_correlation_age) = \
                self.save_fig(measure, "prb_regression_by_age")
            return (res.pvalue_correlation_age_male,
                    res.pvalue_correlation_age_female)
        return None, None

    def build_regression_by_nviq(self, measure, res):
        nviq_id = self.pheno_db.get_nonverbal_iq_measure_id(measure.measure_id)
        if nviq_id is None:
            return None, None
        if measure.measure_id == nviq_id:
            return None, None
        age_id = self.pheno_db.get_age_measure_id(measure.measure_id)
        if measure.measure_id == age_id:
            return None, None

        df = self.load_measure_and_nonverbal_iq(measure)
        if df is None:
            return None, None

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            res_male, res_female = draw_linregres(
                dd, 'nonverbal_iq', measure.measure_id, jitter=0.1)
            res.pvalue_correlation_nviq_male = \
                res_male.pvalues['nonverbal_iq'] \
                if res_male is not None else None
            res.pvalue_correlation_nviq_female = \
                res_female.pvalues['nonverbal_iq'] \
                if res_female is not None else None

            (res.figure_correlation_nviq_small,
             res.figure_correlation_nviq) = self.save_fig(
                 measure, "prb_regression_by_nviq")
            return (res.pvalue_correlation_nviq_male,
                    res.pvalue_correlation_nviq_female)
        return None, None

    def build_values_violinplot(self, measure, res):
        df = self.load_measure(measure)
        draw_measure_violinplot(df, measure.measure_id)
        (res.figure_distribution_small,
         res.figure_distribution) = self.save_fig(measure, "violinplot")

    def build_values_categorical_distribution(self, measure, res):
        df = self.load_measure(measure)
        draw_categorical_violin_distribution(df, measure.measure_id)
        (res.figure_distribution_small,
         res.figure_distribution) = self.save_fig(measure, "distribution")

    def build_values_ordinal_distribution(self, measure, res):
        df = self.load_measure(measure)
        draw_ordinal_violin_distribution(df, measure.measure_id)
        (res.figure_distribution_small,
         res.figure_distribution) = self.save_fig(measure, "distribution")

    def dump_browser_variable(self, var):
        print('-------------------------------------------')
        print(var.measure_id)
        print('-------------------------------------------')
        print('instrument: {}'.format(var.instrument_name))
        print('measure:    {}'.format(var.measure_name))
        print('type:       {}'.format(var.measure_type))
        print('domain:     {}'.format(var.values_domain))
        print('-------------------------------------------')

    def handle_measure(self, measure):
        v = VariableBrowserModel()
        v.measure_id = measure.measure_id
        v.instrument_name = measure.instrument_name
        v.measure_name = measure.measure_name
        v.measure_type = measure.measure_type
        v.values_domain = measure.value_domain

        if measure.measure_type == 'continuous':
            self.build_values_violinplot(measure, v)
            self.build_regression_by_nviq(measure, v)
            self.build_regression_by_age(measure, v)
        elif measure.measure_type == 'ordinal':
            self.build_values_ordinal_distribution(measure, v)
            self.build_regression_by_nviq(measure, v)
            self.build_regression_by_age(measure, v)
        else:
            self.build_values_categorical_distribution(measure, v)
        return v

    def run(self):
        with VariableBrowserModelManager(dbfile=self.browser_db) as vm:
            vm.drop_tables()
            vm.create_tables()

            for instrument in self.pheno_db.instruments.values():
                progress_nl()
                for measure in instrument.measures.values():
                    progress()
                    var = self.handle_measure(measure)
                    vm.save(var)
