'''
Created on Apr 10, 2017

@author: lubo
'''
import os
import matplotlib.pyplot as plt
from DAE import pheno
from pheno_browser.graphs import draw_linregres, draw_measure_violinplot,\
    draw_distribution


class PreparePhenoBrowserBase(object):

    LARGE_DPI = 300
    SMALL_DPI = 16

    def __init__(self, pheno_db, output_dir):
        assert os.path.exists(output_dir)
        self.output_dir = output_dir
        self.pheno_db = pheno.get_pheno_db(pheno_db)

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

    def save_fig(self, measure, suffix):
        #         filepath = self.figure_filepath(
        #             measure, "{}_small".format(suffix))
        #         plt.savefig(filepath, dpi=self.SMALL_DPI)

        filepath = self.figure_filepath(measure, suffix)
        plt.savefig(filepath, dpi=self.LARGE_DPI)
        plt.close()
        return filepath

    def build_regression_by_age(self, measure):
        df = self.load_measure_and_age(measure)
        if df is None:
            return None, None

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            print(dd.head())
            res_male, res_female = draw_linregres(
                dd, 'age', measure.measure_id, jitter=0.3)
            self.save_fig(measure, "prb_regression_by_age")
            return res_male, res_female
        return None, None

    def build_regression_by_nviq(self, measure):
        df = self.load_measure_and_nonverbal_iq(measure)
        if df is None:
            return None, None

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            res_male, res_female = draw_linregres(
                dd, 'nonverbal_iq', measure.measure_id, jitter=0.3)
            # self._figure_caption(caption)
            self.save_fig(measure, "prb_regression_by_nviq")
            return res_male, res_female
        return None, None

    def build_values_figure(self, measure):
        df = self.load_measure(measure)
        draw_measure_violinplot(df, measure.measure_id)
        self.save_fig(measure, "violinplot")

    def build_values_distribution(self, measure):
        df = self.load_measure(measure)
        draw_distribution(df, measure.measure_id)
        self.save_fig(measure, "distribution")

    def run(self):
        for instrument in self.pheno_db.instruments.values():
            print("processing instrument: {}".format(instrument.name))
            for measure in instrument.measures.values():
                print("\tprocessing measure: {}".format(measure.name))
                if measure.measure_type == 'continuous':
                    self.build_values_distribution(measure)
                    break
