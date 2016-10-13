'''
Created on Oct 12, 2016

@author: lubo
'''
import sys

import matplotlib.pyplot as plt
from pheno.prepare.report import PhenoReportBase, parse_args, draw_linregres


class ProbandsPhenoReport(PhenoReportBase):
    FIGSIZE = (10, 5)
    RFIGSIZE = (10, 8)

    def __init__(self, args):
        super(ProbandsPhenoReport, self).__init__(args)

    def out_measure_distribution(self, m):
        title = 'Values Distribution'
        self.out_title(title, self.H4)

        df = self.load_measure(m)

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            self._out_measure_distribution(dd, 'Probands', m, 'prb')

    def out_measure_regressions_by_age(self, m):
        title = 'Fitting OLS by Age'
        self.out_title(title, self.H4)

        df = self.load_measure(m)

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            self.out_title("Probands", self.H5)
            plt.figure(figsize=self.FIGSIZE)
            res_male, res_female = draw_linregres(
                dd, 'pheno_common.age', m.measure_id, jitter=0.3)
            caption = 'Probands: {} ~ {}'.format(m.name, 'age')
            self._figure_caption(caption)
            linkpath = self.save_fig(m, "prb_regression_by_age")

            self._out_figure(linkpath, caption)

            with open(self.outpath, 'a') as out:
                out.write(
                    'Probands male model: slope: {0:.2G}; intercept: {1:.2G}; '
                    'pvalue: {2:.2G}\n\n'.format(
                        res_male.params[1], res_male.params[0],
                        res_male.pvalues[1]))
            with open(self.outpath, 'a') as out:
                out.write(
                    'Probands female model: slope: {0:.2G}; '
                    'intercept: {1:.2G}; '
                    'pvalue: {2:.2G}\n\n'.format(
                        res_female.params[1], res_female.params[0],
                        res_female.pvalues[1]))

    def out_measure(self, m):
        self.out_measure_name(m)
        self.out_measure_type(m)
        self.out_measure_description(m)

        self.out_measure_individuals_summary(m)
        self.out_measure_values_figure(m)

        self.out_measure_distribution(m)

        self.out_measure_regressions_by_age(m)
#         self.out_measure_regressions_by_nviq(m)

    def test_run(self):
        self.reset()

        title = 'Probands PhenoDB Instruments Description'
        self.out_title(title, self.H1)
        # for instrument in self.phdb.instruments.values():
        instrument = self.phdb.instruments['ssc_commonly_used']
        self.out_instrument(instrument)
        for m in instrument.measures.values():
            if m.stats == 'continuous':
                print("handling measure: {}".format(m.measure_id))
                self.out_measure(m)


if __name__ == "__main__":

    args = parse_args(sys.argv[1:])

    report = ProbandsPhenoReport(args)
    report.test_run()
