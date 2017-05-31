'''
Created on Apr 10, 2017

@author: lubo
'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

from collections import defaultdict
import traceback


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
    name1 = col1.split('.')[-1]
    name2 = col2.split('.')[-1]
    return (name1, name2)


def male_female_colors():
    [color_male, color_female] = gender_palette()
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
    male_patch = mpatches.Patch(color=color_male, label='M')
    female_patch = mpatches.Patch(color=color_female, label='F')
    ax.legend(handles=[male_patch, female_patch], title='gender')


def draw_linregres(df, col1, col2, jitter=None, ax=None):
    if ax is None:
        ax = plt.gca()

    dd = df.dropna()

    dmale = dd[dd.gender == 'M']
    dfemale = dd[dd.gender == 'F']

    name1, name2 = names(col1, col2)
    ax.set_xlabel(name1)
    ax.set_ylabel(name2)

    try:
        x = dmale[col1]
        X = sm.add_constant(x)
        y = dmale[col2]
        res_male = sm.OLS(y, X).fit()
    except ValueError:
        traceback.print_exc()
        res_male = None

    try:
        x = dfemale[col1]
        X = sm.add_constant(x)
        y = dfemale[col2]
        res_female = sm.OLS(y, X).fit()
    except ValueError:
        traceback.print_exc()
        res_female = None

    if jitter is None:
        jmale1 = jmale2 = np.zeros(len(dmale[col1]))
        jfemale1 = jfemale2 = np.zeros(len(dfemale[col1]))
    else:
        jmale1 = np.random.uniform(-jitter, jitter, len(dmale[col1]))
        jmale2 = np.random.uniform(-jitter, jitter, len(dmale[col2]))

        jfemale1 = np.random.uniform(-jitter, jitter, len(dfemale[col1]))
        jfemale2 = np.random.uniform(-jitter, jitter, len(dfemale[col2]))

    [color_male, color_female] = gender_palette_light()
    ax.plot(
        dmale[col1] + jmale1,
        dmale[col2] + jmale2,
        '.', color=color_male, ms=4,
        label='male')
    ax.plot(
        dfemale[col1] + jfemale1,
        dfemale[col2] + jfemale2,
        '.', color=color_female, ms=4,
        label='female')

    [color_male, color_female] = gender_palette()
    if res_male:
        ax.plot(dmale[col1], res_male.predict(), color=color_male)
    if res_female:
        ax.plot(dfemale[col1], res_female.predict(), color=color_female)

    male_female_legend(color_male, color_female, ax)
    return res_male, res_female


def draw_distribution(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    color_male, color_female = male_female_colors()
    ax.hist(
        [
            df[df.gender == 'F'][measure_id],
            df[df.gender == 'M'][measure_id]
        ],
        color=[color_female, color_male],
        stacked=True,
        bins=20,
        normed=False)
    # sns.kdeplot(df[col], ax=ax, color=extra_color())
    male_female_legend(color_male, color_female, ax)

    ax.set_xlabel(measure_id)
    ax.set_ylabel('count')


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


def gender_palette_light():
    palette = sns.diverging_palette(240, 10, s=80, l=77, n=2)  # @IgnorePep8
    return palette


def gender_palette():
    palette = sns.diverging_palette(240, 10, s=80, l=50, n=2)  # @IgnorePep8
    return palette


def draw_measure_violinplot(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    palette = gender_palette()
    sns.violinplot(
        data=df, x='role', y=measure_id, hue='gender',
        order=['prb', 'sib', 'parent'], hue_order=['M', 'F'],
        linewidth=1, split=True,
        scale='count',
        scale_hue=False,
        palette=palette,
        saturation=1)

    palette = gender_palette_light()
    sns.stripplot(
        data=df, x='role', y=measure_id, hue='gender',
        order=['prb', 'sib', 'parent'], hue_order=['M', 'F'],
        jitter=0.025, size=2,
        palette=palette,
        linewidth=0.1)

    labels = role_labels(df)
    plt.xticks([0, 1, 2], labels)


def draw_categorical_violin_distribution(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    df = df.copy()

    color_male, color_female = male_female_colors()

    values_domain = sorted(df[measure_id].unique())
    y_locations = np.arange(len(values_domain))
    df[measure_id].replace(dict(zip(values_domain, y_locations)), inplace=True)

    bin_edges = y_locations - 0.5
    centers = bin_edges
    heights = 0.8

    hist_range = (np.min(y_locations), np.max(y_locations))

    datasets = []
    binned_datasets = []

    for role in ['prb', 'sib', 'parent']:
        df_role = df[df.role == role]

        df_male = df_role[df_role.gender == 'M']
        df_female = df_role[df_role.gender == 'F']

        mdata = df_male[measure_id].values
        fdata = df_female[measure_id].values
        datasets.append((mdata, fdata))

        binned_datasets.append([
            np.histogram(d, range=hist_range, bins=len(y_locations))[0]
            for d in [mdata, fdata]
        ])

    binned_maximum = np.max(
        [np.max([np.max(m), np.max(f)]) for (m, f) in binned_datasets]
    )

    x_locations = np.arange(0, 3 * 2 * binned_maximum, 2 * binned_maximum)

    _fig, ax = plt.subplots()
    for count, (male, female) in enumerate(binned_datasets):
        x_loc = x_locations[count]

        lefts = x_loc - male
        ax.barh(centers, male, height=heights, left=lefts, color=color_male)
        ax.barh(centers, female, height=heights,
                left=x_loc, color=color_female)

    ax.set_yticks(y_locations)
    ax.set_yticklabels(values_domain)
    ax.set_xlim(2 * -binned_maximum, 6 * binned_maximum)
    ax.set_ylim(-1, np.max(y_locations) + 1)

    ax.set_ylabel(measure_id)
    labels = role_labels(df)
    plt.xticks(x_locations, labels)

    male_female_legend(color_male, color_female, ax)


def draw_ordinal_violin_distribution(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    df = df.copy()

    color_male, color_female = male_female_colors()
    df[measure_id] = df[measure_id].apply(lambda v: round(v))

    values_domain = sorted(df[measure_id].unique())
    y_locations = np.arange(np.min(values_domain), np.max(values_domain) + 1)

    bin_edges = y_locations - 0.5
    centers = bin_edges
    heights = 0.8

    hist_range = (np.min(y_locations), np.max(y_locations))

    datasets = []
    binned_datasets = []

    for role in ['prb', 'sib', 'parent']:
        df_role = df[df.role == role]

        df_male = df_role[df_role.gender == 'M']
        df_female = df_role[df_role.gender == 'F']

        mdata = df_male[measure_id].values
        fdata = df_female[measure_id].values
        datasets.append((mdata, fdata))

        binned_datasets.append([
            np.histogram(d, range=hist_range, bins=len(y_locations))[0]
            for d in [mdata, fdata]
        ])

    binned_maximum = np.max(
        [np.max([np.max(m), np.max(f)]) for (m, f) in binned_datasets]
    )

    x_locations = np.arange(0, 3 * 2 * binned_maximum, 2 * binned_maximum)

    _fig, ax = plt.subplots()
    for count, (male, female) in enumerate(binned_datasets):
        x_loc = x_locations[count]

        lefts = x_loc - male
        ax.barh(centers, male, height=heights, left=lefts, color=color_male)
        ax.barh(centers, female, height=heights,
                left=x_loc, color=color_female)

    ax.set_yticks(y_locations)
    ax.set_yticklabels(y_locations)
    ax.set_xlim(2 * -binned_maximum, 6 * binned_maximum)
    ax.set_ylim(np.min(y_locations) - 1, np.max(y_locations) + 1)

    ax.set_ylabel(measure_id)
    labels = role_labels(df)
    plt.xticks(x_locations, labels)

    male_female_legend(color_male, color_female, ax)
