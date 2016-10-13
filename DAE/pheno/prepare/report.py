'''
Created on Sep 17, 2016

@author: lubo
'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

from pheno.pheno_db import PhenoDB
import sys
import argparse
import os
from collections import OrderedDict
from collections import defaultdict

FIGSIZE = (10, 6)


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


def roles():
    return [
        'all',
        'M',
        'F',
        'prb',
        'prbM',
        'prbF',
        'sib',
        'sibM',
        'sibF',
        'parents',
        'dad',
        'mom',
    ]


def roles_indices(df):
    return [
        ('all', None),
        ('M', df.gender == 'M'),
        ('F', df.gender == 'F'),

        ('prb', df.role == 'prb'),
        ('prbM', np.logical_and(df.role == 'prb', df.gender == 'M')),
        ('prbF', np.logical_and(df.role == 'prb', df.gender == 'F')),

        ('sib', df.role == 'sib'),
        ('sibM', np.logical_and(df.role == 'sib', df.gender == 'M')),
        ('sibF', np.logical_and(df.role == 'sib', df.gender == 'F')),

        ('parents', np.logical_or(df.role == 'dad', df.role == 'mom')),
        ('dad', df.role == 'dad'),
        ('mom', df.role == 'mom'),
    ]


def roles_split(df, measure_ids):
    data = defaultdict(list)
    for (role, index) in roles_indices(df):
        if index is None:
            size = len(df)
            gender = df['gender'].values
        else:
            size = np.sum(index)
            gender = df[index]['gender'].values

        data['role'].append([role] * size)
        data['gender'].append(gender)

        for mid in measure_ids:
            if index is None:
                data[mid].append(df[mid].values)
            else:
                data[mid].append(df[index][mid].values)

    data = {
        key: np.hstack(value) for (key, value) in data.items()
    }
    return pd.DataFrame(data=data)


def names(col1, col2):
    assert '.' in col1
    assert '.' in col2
    name1 = col1.split('.')[1]
    name2 = col2.split('.')[1]
    return (name1, name2)


def male_female_colors():
    colors = iter(plt.rcParams['axes.prop_cycle'])
    color_male = colors.next()['color']
    color_female = colors.next()['color']
    return color_male, color_female


def extra_color():
    colors = iter(plt.rcParams['axes.prop_cycle'])
    colors.next()
    colors.next()
    return colors.next()['color']


def male_female_legend(color_male, color_female, ax=None):
    if ax is None:
        ax = plt.gca()

    import matplotlib.patches as mpatches
    male_patch = mpatches.Patch(color=color_male, label='Male')
    female_patch = mpatches.Patch(color=color_female, label='Female')
    ax.legend(handles=[male_patch, female_patch])


def draw_linregres(df, col1, col2, jitter=None, ax=None):
    if ax is None:
        ax = plt.gca()

    dd = df.dropna()

    dmale = dd[dd.gender == 'M']
    dfemale = dd[dd.gender == 'F']

    name1, name2 = names(col1, col2)
    ax.set_xlabel(name1)
    ax.set_ylabel(name2)

    x = dmale[col1]
    X = sm.add_constant(x)
    y = dmale[col2]
    res_male = sm.OLS(y, X).fit()

    x = dfemale[col1]
    X = sm.add_constant(x)
    y = dfemale[col2]
    res_female = sm.OLS(y, X).fit()

    color_male, color_female = male_female_colors()

    if jitter is None:
        jmale1 = jmale2 = np.zeros(len(dmale[col1]))
        jfemale1 = jfemale2 = np.zeros(len(dfemale[col1]))
    else:
        jmale1 = np.random.uniform(-jitter, jitter, len(dmale[col1]))
        jmale2 = np.random.uniform(-jitter, jitter, len(dmale[col2]))

        jfemale1 = np.random.uniform(-jitter, jitter, len(dfemale[col1]))
        jfemale2 = np.random.uniform(-jitter, jitter, len(dfemale[col2]))

    ax.plot(
        dmale[col1] + jmale1,
        dmale[col2] + jmale2,
        '.', color=color_male, ms=5,
        label='male')
    ax.plot(dmale[col1], res_male.predict(), color=color_male)

    ax.plot(
        dfemale[col1] + jfemale1,
        dfemale[col2] + jfemale2,
        '.', color=color_female, ms=5,
        label='female')
    ax.plot(dfemale[col1], res_female.predict(), color=color_female)

    male_female_legend(color_male, color_female, ax)
    return res_male, res_female


def draw_distribution(df, col, ax=None):
    if ax is None:
        ax = plt.gca()

    color_male, color_female = male_female_colors()
    ax.hist(
        [
            df[df.gender == 'F'][col],
            df[df.gender == 'M'][col]
        ],
        color=[color_female, color_male],
        stacked=True,
        bins=20,
        normed=True)
    sns.kdeplot(df[col], ax=ax, color=extra_color())
    male_female_legend(color_male, color_female, ax)


# def _measure_df_gender_split(df, col):
#     data = [
#         df[col],
#         df[df.gender == 'M'][col],
#         df[df.gender == 'F'][col]
#     ]
#     return data
#
#
# def _measure_df_split(df, col):
#     data = _measure_df_gender_split(df, col)
#     data.extend(_measure_df_gender_split(df[df.role == 'prb'], col))
#     data.extend(_measure_df_gender_split(df[df.role == 'sib'], col))
#     data.extend(_measure_df_gender_split(
#         df[np.logical_or(df.role == 'mom', df.role == 'dad')], col))
#
#     labels = [
#         'All ({})'.format(len(data[0])),
#         'M ({})'.format(len(data[1])),
#         'F ({})'.format(len(data[2])),
#         'prb All ({})'.format(len(data[3])),
#         'prb M ({})'.format(len(data[4])),
#         'prb F ({})'.format(len(data[5])),
#         'sib All ({})'.format(len(data[6])),
#         'sib M ({})'.format(len(data[7])),
#         'sib F ({})'.format(len(data[8])),
#         'Parents All ({})'.format(len(data[9])),
#         'dad ({})'.format(len(data[10])),
#         'mom ({})'.format(len(data[11]))]
#     return data, labels


def role_counts(df):
    counts = {
        'prb': len(df[df.role == 'prb']),
        'prbM': len(df[np.logical_and(df.role == 'prb', df.gender == 'M')]),
        'prbF': len(df[np.logical_and(df.role == 'prb', df.gender == 'F')]),

        'sib': len(df[df.role == 'sib']),
        'sibM': len(df[np.logical_and(df.role == 'sib', df.gender == 'M')]),
        'sibF': len(df[np.logical_and(df.role == 'sib', df.gender == 'F')]),

        'parent': len(df[df.role == 'parent']),
        'parentM': len(df[np.logical_and(
            df.role == 'parent', df.gender == 'M')]),
        'parentF': len(df[np.logical_and(
            df.role == 'parent', df.gender == 'F')]),
    }
    return counts


def role_labels(df):
    counts = role_counts(df)
    return [
        "prb: {prb:>4d}\n  M: {prbM:>4d}\n  F: {prbF:>4d}".format(**counts),
        "sib: {sib:>4d}\n  M: {sibM:>4d}\n  F: {sibF:>4d}".format(**counts),
        "parent: {parent:>4d}\n   dad: {parentM:>4d}\n   mom: {parentF:>4d}"
        .format(**counts),
    ]


def draw_measure_violinplot(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    palette = sns.diverging_palette(240, 10, s=80, l=50, n=2, )
    sns.violinplot(
        data=df, x='role', y=measure_id, hue='gender',
        order=['prb', 'sib', 'parent'], hue_order=['M', 'F'],
        linewidth=1, split=True,
        scale='count',
        palette=palette)

    palette = sns.diverging_palette(240, 10, s=80, l=77, n=2, )
    sns.stripplot(
        data=df, x='role', y=measure_id, hue='gender',
        order=['prb', 'sib', 'parent'], hue_order=['M', 'F'],
        jitter=0.025, size=2,
        palette=palette,
        linewidth=0.1)

    labels = role_labels(df)
    plt.xticks([0, 1, 2], labels)

# def draw_measure_violinplot(df, col, ax=None):
#     if ax is None:
#         ax = plt.gca()
#
#     data, labels = _measure_df_split(df, col)
#
#     sns.violinplot(
#         data=data,
#         scale='count',
#         linewidth=0.1)
#     plt.xticks(range(len(labels)), labels, rotation='vertical')


#     pos = range(1, len(labels) + 1)
#     plt.xticks(pos, labels, rotation='vertical')
#     for index, df in enumerate(data):
#         pos = index + 1
#         if len(df) > 0:
#             ax.violinplot(df.values, [pos], points=20, widths=1.0)


class PhenoReportBase(object):

    def __init__(self, args):
        self.args = args
        self.outfile = "source/index.rst"
        self.outpath = os.path.join(self.args.output, self.outfile)

        self.phdb = PhenoDB()
        self.phdb.load()

    def load_measure(self, m):
        df = self.phdb.get_persons_values_df(
            ['pheno_common.age', m.measure_id])
        df.loc[df.role == 'mom', 'role'] = 'parent'
        df.loc[df.role == 'dad', 'role'] = 'parent'
        return df

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
            ('parent', [
                len(df[np.logical_and(df.role == 'parent', df.gender == 'M')][
                    m.measure_id]),
                len(df[np.logical_and(df.role == 'parent', df.gender == 'F')][
                    m.measure_id]),
                len(df[df.role == 'parent'][m.measure_id]),
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
        out.write('\n')
        out.write('\n')
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

            out.write(m.description.encode('utf-8'))
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

    def out_measure_values_figure(self, m):
        caption = 'Measure\n{}'.format(m.measure_id)
        df = self.load_measure(m)

        draw_measure_violinplot(df, m.measure_id)
        self._figure_caption(caption)
        linkpath = self.save_fig(m, "violinplot")
        self._out_figure(linkpath, caption)

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

    def _out_measure_distribution(self, df, title, m, role):
        self.out_title(title, self.H5)
        plt.figure(figsize=self.FIGSIZE)
        draw_distribution(df, m.measure_id)

        caption = '{}: {} distribution'.format(title, m.name)
        self._figure_caption(caption)
        linkpath = self.save_fig(
            m, "{}_distribution".format(role))
        self._out_figure(linkpath, caption)

    def out_measure_type(self, m):
        title = "Measure Type: {}".format(m.stats)
        line = len(title) * self.H4
        with open(self.outpath, 'a') as out:
            self._out_header(out, title, line)

    def out_instrument(self, instrument):
        with open(self.outpath, 'a') as out:
            title = 'Instrument: {}'.format(instrument.name)
            line = len(title) * self.H2
            self._out_header(out, title, line)

    def out_title(self, title, header):
        with open(self.outpath, 'a') as out:
            line = len(title) * header
            self._out_header(out, title, line)

    def reset(self):
        with open(self.outpath, 'w') as out:
            out.write('\n')


class PhenoReport(PhenoReportBase):
    FIGSIZE = (10, 5)
    RFIGSIZE = (10, 8)

    def __init__(self, args):
        super(PhenoReport, self).__init__(args)

    def out_measure_distribution(self, m):
        title = 'Values Distribution'
        self.out_title(title, self.H4)

        df = self.phdb.get_persons_values_df(
            [m.measure_id])
        df = roles_split(df, [m.measure_id])

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            self._out_measure_distribution(dd, 'Probands', m, 'prb')
        dd = df[df.role == 'sib']
        if len(dd) > 5:
            self._out_measure_distribution(dd, 'Siblings', m, 'sib')

    def out_measure_regressions_by_age(self, m):
        title = 'Fitting OLS by Age'
        self.out_title(title, self.H4)

        df = self.phdb.get_persons_values_df(
            ['pheno_common.age', m.measure_id])

        df = roles_split(df, ['pheno_common.age', m.measure_id])

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

        dd = df[df.role == 'sib']
        if len(dd) > 5:
            self.out_title("Siblings", self.H5)
            plt.figure(figsize=self.FIGSIZE)
            res_male, res_female = draw_linregres(
                dd, 'pheno_common.age', m.measure_id)
            caption = 'Siblings: {} ~ {}'.format(m.name, 'age')
            self._figure_caption(caption)
            linkpath = self.save_fig(m, "sib_regression_by_age")

            self._out_figure(linkpath, caption)

            with open(self.outpath, 'a') as out:
                out.write(
                    'Siblings male model: slope: {0:.2G}; intercept: {1:.2G}; '
                    'pvalue: {2:.2G}\n\n'.format(
                        res_male.params[1], res_male.params[0],
                        res_male.pvalues[1]))
            with open(self.outpath, 'a') as out:
                out.write(
                    'Siblings female model: slope: {0:.2G}; '
                    'intercept: {1:.2G}; '
                    'pvalue: {2:.2G}\n\n'.format(
                        res_female.params[1], res_female.params[0],
                        res_female.pvalues[1]))

    def out_measure_regressions_by_nviq(self, m):

        title = 'Fitting OLS by Non Verbal IQ'
        self.out_title(title, self.H4)

        df = self.phdb.get_persons_values_df(
            ['pheno_common.non_verbal_iq', m.measure_id])

        df = roles_split(df, ['pheno_common.non_verbal_iq', m.measure_id])

        dd = df[df.role == 'prb']
        if len(dd) > 5:
            self.out_title("Probands", self.H5)
            plt.figure(figsize=self.FIGSIZE)
            res_male, res_female = draw_linregres(
                dd, 'pheno_common.non_verbal_iq', m.measure_id)
            caption = 'Probands: {} ~ {}'.format(m.name, 'non_verbal_iq')
            self._figure_caption(caption)
            linkpath = self.save_fig(m, "prb_regression_by_non_verbal_iq")

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

        dd = df[df.role == 'sib']
        if len(dd) > 5:
            self.out_title("Siblings", self.H5)
            plt.figure(figsize=self.FIGSIZE)
            res_male, res_female = draw_linregres(
                dd, 'pheno_common.non_verbal_iq', m.measure_id)
            caption = 'Siblings: {} ~ {}'.format(m.name, 'non_verbal_iq')
            self._figure_caption(caption)
            linkpath = self.save_fig(m, "sib_regression_by_non_verbal_iq")

            self._out_figure(linkpath, caption)
            with open(self.outpath, 'a') as out:
                out.write(
                    'Siblings male model: slope: {0:.2G}; intercept: {1:.2G}; '
                    'pvalue: {2:.2G}\n\n'.format(
                        res_male.params[1], res_male.params[0],
                        res_male.pvalues[1]))
            with open(self.outpath, 'a') as out:
                out.write(
                    'Siblings female model: slope: {0:.2G}; '
                    'intercept: {1:.2G}; '
                    'pvalue: {2:.2G}\n\n'.format(
                        res_female.params[1], res_female.params[0],
                        res_female.pvalues[1]))

    def out_measure(self, m):
        self.out_measure_name(m)
        self.out_measure_type(m)
        self.out_measure_description(m)

        _counts_df = self.out_measure_individuals_summary(m)
        self.out_measure_values_figure(m)

        self.out_measure_distribution(m)

        self.out_measure_regressions_by_age(m)
        self.out_measure_regressions_by_nviq(m)

    def test_run(self):
        self.reset()

        title = 'PhenoDB Instruments Description'
        self.out_title(title, self.H1)
        # for instrument in self.phdb.instruments.values():
        instrument = self.phdb.instruments['ssc_commonly_used']
        self.out_instrument(instrument)
        for m in instrument.measures.values()[:20]:
            if m.stats == 'continuous':
                print("handling measure: {}".format(m.measure_id))
                self.out_measure(m)

if __name__ == "__main__":

    args = parse_args(sys.argv[1:])

    report = PhenoReport(args)
    report.test_run()
