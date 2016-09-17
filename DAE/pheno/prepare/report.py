'''
Created on Sep 17, 2016

@author: lubo
'''

import numpy as np
import pylab as pl
import pandas as pd
import matplotlib.pyplot as plt
from pheno.pheno_db import PhenoDB
import sys
import argparse
import os
from collections import OrderedDict


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Tool to precompute caches for DAE.')

    parser.add_argument(
        '--output', '-o',
        dest='output',
        default='.',
        help='output directory to store the report')

    # Process arguments
    return parser.parse_args(argv)


class PhenoReport(object):

    def __init__(self, args):
        self.args = args
        self.outfile = "pheno_report.rst"
        self.outpath = os.path.join(self.args.output, self.outfile)

    def measure_gender_boxplots(self, m, df):
        data = [
            df[m.measure_id],
            df[df.gender == 'M'][m.measure_id],
            df[df.gender == 'F'][m.measure_id],
        ]
        labels = [
            'All ({})'.format(len(data[0])),
            'M ({})'.format(len(data[1])),
            'F ({})'.format(len(data[2])),
        ]
        plt.boxplot(data, labels=labels, showmeans=True)

    def savefig(self, measure, suffix, dpi=120):
        filename = "{}.{}.png".format(
            measure.measure_id, suffix)
        filepath = os.path.join(self.args.output, 'figs', filename)
        plt.savefig(filepath, dpi=dpi)

    def individuals_counts_df(self, m, df):

        d = OrderedDict([
            ('prb', [
                len(df[np.logical_and(df.role == 'prb', df.gender == 'M')][
                    m.measure_id]),
                len(df[np.logical_and(df.role == 'prb', df.gender == 'F')][
                    m.measure_id]),
                len(df[df.role == 'prb'][m.measure_id]),
            ]),
            ('sib', [
                len(df[np.logical_and(df.role == 'sib', df.gender == 'M')][
                    m.measure_id]),
                len(df[np.logical_and(df.role == 'sib', df.gender == 'F')][
                    m.measure_id]),
                len(df[df.role == 'sib'][m.measure_id]),
            ]),
            ('parents', [
                len(df[df.role == 'dad'][
                    m.measure_id]),
                len(df[df.role == 'mom'][
                    m.measure_id]),
                len(df[np.logical_or(df.role == 'mom', df.role == 'dad')][
                    m.measure_id]),
            ]),
            ('ALL', [
                len(df[df.gender == 'M'][
                    m.measure_id]),
                len(df[df.gender == 'F'][
                    m.measure_id]),
                len(df[m.measure_id]),
            ]),

        ])
        res = pd.DataFrame(d, index=['M', 'F', 'ALL'])
        print(res.head())
        return res

    def df_table(self, df):
        from tabulate import tabulate
        with open(self.outpath, 'a') as out:
            out.write(tabulate(df, headers="keys", tablefmt="grid"))
            out.write('\n')

    def run(self):
        phdb = PhenoDB()
        phdb.load()

        instrument = phdb.instruments['abc']
        m = instrument.measures.values()[1]

        df = phdb.get_persons_values_df([m.measure_id])
        tdf = self.individuals_counts_df(m, df)
        self.df_table(tdf)

        self.measure_gender_boxplots(m, df)
        self.savefig(m, "boxplot_all")


if __name__ == "__main__":

    args = parse_args(sys.argv[1:])

    report = PhenoReport(args)
    report.run()
