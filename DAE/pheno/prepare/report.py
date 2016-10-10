'''
Created on Sep 17, 2016

@author: lubo
'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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


def build_measure_df(df, measure_id):
    values = df[measure_id].values
    roles = [['ALL'] * len(values)]
    data = [values]

    values = df[df.gender == 'M'][measure_id].values
    roles.append(['M'] * len(values))
    data.append(values)

    values = df[df.gender == 'F'][measure_id].values
    roles.append(['F'] * len(values))
    data.append(values)

    values = df[df.role == 'prb'][measure_id].values
    roles.append(['prb'] * len(values))
    data.append(values)

    values = df[np.logical_and(
        df.role == 'prb', df.gender == 'M')][measure_id].values
    roles.append(['prbM'] * len(values))
    data.append(values)

    values = df[np.logical_and(df.role == 'prb', df.gender == 'F')][
        measure_id].values
    roles.append(['prbF'] * len(values))
    data.append(values)

    values = df[df.role == 'sib'][measure_id].values
    roles.append(['sib'] * len(values))
    data.append(values)

    values = df[np.logical_and(df.role == 'sib', df.gender == 'M')][
        measure_id].values
    roles.append(['sibM'] * len(values))
    data.append(values)

    values = df[np.logical_and(df.role == 'sib', df.gender == 'F')][
        measure_id].values
    roles.append(['sibF'] * len(values))
    data.append(values)

    values = df[np.logical_or(df.role == 'dad', df.role == 'mom')][
        measure_id].values
    roles.append(['parents'] * len(values))
    data.append(values)

    values = df[df.role == 'dad'][measure_id].values
    roles.append(['dad'] * len(values))
    data.append(values)

    values = df[df.role == 'mom'][measure_id].values
    roles.append(['mom'] * len(values))
    data.append(values)

    return pd.DataFrame(
        data={
            'role': np.hstack(roles),
            'value': np.hstack(data)
        })


def build_measure_df_labels(dd):
    labels = [
        'All ({})'.format(np.sum(dd.role == 'ALL')),
        'M ({})'.format(np.sum(dd.role == 'M')),
        'F ({})'.format(np.sum(dd.role == 'F')),
        'prb All ({})'.format(np.sum(dd.role == 'prb')),
        'prb M ({})'.format(np.sum(dd.role == 'prbM')),
        'prb F ({})'.format(np.sum(dd.role == 'prbF')),
        'sib All ({})'.format(np.sum(dd.role == 'sib')),
        'sib M ({})'.format(np.sum(dd.role == 'sibM')),
        'sib F ({})'.format(np.sum(dd.role == 'sibF')),
        'Parents All ({})'.format(np.sum(dd.role == 'parents')),
        'dad ({})'.format(np.sum(dd.role == 'dad')),
        'mom ({})'.format(np.sum(dd.role == 'mom'))]
    return labels


class MeasureData(object):

    def __init__(self, data, labels):
        self.data = data
        self.labels = labels

    def get(self, label, default):
        print("label: {}; default: {}".format(label, default))
        if label not in self.labels:
            return self.data[0]
        index = self.labels.index(label)
        return self.data[index]


class PhenoReport(object):
    FIGSIZE = (10, 5)

    def __init__(self, args):
        self.args = args
        self.outfile = "source/index.rst"
        self.outpath = os.path.join(self.args.output, self.outfile)

        self.phdb = PhenoDB()
        self.phdb.load()

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
        plt.boxplot(data, showmeans=True)
        plt.xticks(range(1, len(labels) + 1), labels, rotation='vertical')

    def measure_gender_violinplot(self, m, df):
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
        sns.violinplot(data=data)
        plt.xticks(range(len(labels)), labels, rotation='vertical')

    def _measure_df_gender_split(self, m, df):
        data = [
            df[m.measure_id],
            df[df.gender == 'M'][m.measure_id],
            df[df.gender == 'F'][m.measure_id]
        ]
        return data

    def _measure_df_split(self, m, df):
        data = self._measure_df_gender_split(m, df)
        data.extend(self._measure_df_gender_split(m, df[df.role == 'prb']))
        data.extend(self._measure_df_gender_split(m, df[df.role == 'sib']))
        data.extend(self._measure_df_gender_split(
            m, df[np.logical_or(df.role == 'mom', df.role == 'dad')]))

        labels = [
            'All ({})'.format(len(data[0])),
            'M ({})'.format(len(data[1])),
            'F ({})'.format(len(data[2])),
            'prb All ({})'.format(len(data[3])),
            'prb M ({})'.format(len(data[4])),
            'prb F ({})'.format(len(data[5])),
            'sib All ({})'.format(len(data[6])),
            'sib M ({})'.format(len(data[7])),
            'sib F ({})'.format(len(data[8])),
            'Parents All ({})'.format(len(data[9])),
            'dad ({})'.format(len(data[10])),
            'mom ({})'.format(len(data[11]))]
        return data, labels

    def measure_violinplot(self, m, df):
        data, labels = self._measure_df_split(m, df)
        plt.figure(figsize=self.FIGSIZE)
        sns.violinplot(data=data)
        plt.xticks(range(len(labels)), labels, rotation='vertical')

    def measure_boxplot(self, m, df):
        data, labels = self._measure_df_split(m, df)
        plt.figure(figsize=self.FIGSIZE)
        sns.boxplot(data=data)
        plt.xticks(range(len(labels)), labels, rotation='vertical')

    def measure_stripplot(self, m, df):
        data, labels = self._measure_df_split(m, df)
        plt.figure(figsize=self.FIGSIZE)
        sns.stripplot(data=data, jitter=True)
        plt.xticks(range(len(labels)), labels, rotation='vertical')

    def save_fig(self, measure, suffix, dpi=120):
        filename = "{}.{}.png".format(
            measure.measure_id, suffix)
        linkpath = os.path.join('figs', filename)
        filepath = os.path.join(self.args.output, 'source', linkpath)
        plt.savefig(filepath, dpi=dpi)
        plt.close()

        return linkpath

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
        return res

    H1 = '='
    H2 = '-'
    H3 = '`'
    H4 = "'"
    H5 = '.'

    def _out_df_table(self, out, df):
        from tabulate import tabulate
        out.write(tabulate(df, headers="keys", tablefmt="grid"))
        out.write('\n')

    def _out_header(self, out, title, line):
        out.write('\n')
        out.write(line)
        out.write('\n')
        out.write(title)
        out.write('\n')
        out.write(line)
        out.write('\n\n')

    def out_measure_name(self, m):
        with open(self.outpath, 'a') as out:
            section_title = "Measure: {}".format(m.measure_id)
            section_line = len(section_title) * self.H3
            self._out_header(out, section_title, section_line)

    def out_measure_description(self, m):
        with open(self.outpath, 'a') as out:
            subsection_title = 'Description'
            subsection_line = len(subsection_title) * self.H4
            self._out_header(out, subsection_title, subsection_line)

            out.write(m.description)
            out.write('\n\n\n')

    def out_measure_individuals_summary(self, m):
        with open(self.outpath, 'a') as out:
            title = 'Measured Individuals'
            line = len(title) * self.H4
            self._out_header(out, title, line)

            df = self.phdb.get_persons_values_df([m.measure_id])
            counts_df = self.individuals_counts_df(m, df)
            self._out_df_table(out, counts_df)
            return counts_df

    def _figure_caption(self, caption):
        params = {
            'axes.titlesize': 'large',
        }
        plt.rcParams.update(params)
        plt.title(caption)
        plt.tight_layout()

    def _out_figure(self, linkpath, caption):
        with open(self.outpath, 'a') as out:
            out.write('\n')
            # out.write('.. compound::\n')
            # out.write('  Figure: {}\n\n'.format(caption))
            out.write('.. image:: {}\n'.format(linkpath))
            out.write('   :align: center\n')
            out.write('   :scale: 75%\n\n\n')
            out.write('\n')

    def out_measure_values_figure(self, m):
        caption = 'Measure\n{}'.format(m.measure_id)
        df = self.phdb.get_persons_values_df([m.measure_id])

        self.measure_violinplot(m, df)
        self._figure_caption(caption)
        linkpath = self.save_fig(m, "violinplot")
        self._out_figure(linkpath, caption)

        self.measure_boxplot(m, df)
        self._figure_caption(caption)
        linkpath = self.save_fig(m, "boxplot")
        self._out_figure(linkpath, caption)

        self.measure_stripplot(m, df)
        self._figure_caption(caption)
        linkpath = self.save_fig(m, "stripplot")
        self._out_figure(linkpath, caption)

    def out_measure_type(self, m):
        title = "Measure Type: {}".format(m.stats)
        line = len(title) * self.H4
        with open(self.outpath, 'a') as out:
            self._out_header(out, title, line)

    def out_measure(self, m):
        self.out_measure_name(m)
        self.out_measure_type(m)
        self.out_measure_description(m)

        _counts_df = self.out_measure_individuals_summary(m)
        self.out_measure_values_figure(m)

    def out_instrument(self, instrument):
        with open(self.outpath, 'a') as out:
            title = 'Instrument: {}'.format(instrument.name)
            line = len(title) * self.H2
            self._out_header(out, title, line)

    def out_title(self):
        with open(self.outpath, 'w') as out:
            title = 'PhenoDB Instruments Description'
            line = len(title) * self.H1
            self._out_header(out, title, line)

    def test_run(self):
        self.out_title()

        instrument = self.phdb.instruments['ssc_commonly_used']
        self.out_instrument(instrument)
        for m in instrument.measures.values():
            if m.stats == 'continuous' or m.stats == 'ordinal':
                print("handling measure: {}".format(m.measure_id))
                self.out_measure(m)

if __name__ == "__main__":

    args = parse_args(sys.argv[1:])

    report = PhenoReport(args)
    report.test_run()
