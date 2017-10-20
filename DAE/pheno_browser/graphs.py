'''
Created on Apr 10, 2017

@author: lubo
'''
import textwrap
import matplotlib as mpl
from pheno.common import Role, Gender
mpl.use('PS')

import matplotlib.pyplot as plt  # @IgnorePep8
plt.ioff()

import numpy as np  # @IgnorePep8
import seaborn as sns  # @IgnorePep8
import statsmodels.api as sm  # @IgnorePep8

import traceback  # @IgnorePep8


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
            df[df.gender == Gender.F][measure_id],
            df[df.gender == Gender.M][measure_id]
        ],
        color=[color_female, color_male],
        stacked=True,
        bins=20,
        normed=False)
    # sns.kdeplot(df[col], ax=ax, color=extra_color())
    male_female_legend(color_male, color_female, ax)

    ax.set_xlabel(measure_id)
    ax.set_ylabel('count')


def role_counts(df, role):
    counts = {
        'role_name': textwrap.fill(role, 9),
        'role_total': len(df.query('role == @role')),
        'male_total': len(df.query('role == @role & gender == "M"')),
        'female_total': len(df.query('role == @role & gender == "F"'))
    }
    return counts


def role_labels(df, ordered_roles):
    # counts =
    return [
        "{role_name}:{role_total:>4d}\nM: {male_total:>4d}\n"
        "F: {female_total:>4d}".format(**role_counts(df, role))
        for role in ordered_roles]


def gender_palette_light():
    palette = sns.diverging_palette(240, 10, s=80, l=77, n=2)  # @IgnorePep8
    return palette


def gender_palette():
    palette = sns.diverging_palette(240, 10, s=80, l=50, n=2)  # @IgnorePep8
    return palette


def roles_to_draw(df):
    return df["role"].value_counts().index.values.tolist()


def _enumerate_by_count(df, column_name):
    occurrence_counts = df[column_name].value_counts()
    occurrence_ordered = occurrence_counts.index.values.tolist()
    occurrences_map = {
        value: number for (number, value) in enumerate(occurrence_ordered)
    }

    return (df[column_name].apply(lambda x: occurrences_map[x]),
            occurrence_ordered)


def _enumerate_by_natural_order(df, column_name):
    values_domain = df[column_name].unique()
    values_domain = map(float, values_domain)
    values_domain = sorted(values_domain)
    values_domain = map(str, values_domain)
    return df[column_name].apply(float), values_domain


def draw_measure_violinplot(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    fig = plt.gcf()

    palette = gender_palette()
    roles = roles_to_draw(df)
    assert len(roles) > 0

    fig.set_size_inches(2 + len(roles), 8)

    sns.violinplot(
        data=df, x='role', y=measure_id, hue='gender',
        order=roles, hue_order=['M', 'F'],
        linewidth=1, split=True,
        scale='count',
        scale_hue=False,
        palette=palette,
        saturation=1)

    palette = gender_palette_light()
    sns.stripplot(
        data=df, x='role', y=measure_id, hue='gender',
        order=roles, hue_order=['M', 'F'],
        jitter=0.025, size=2,
        palette=palette,
        linewidth=0.1)

    labels = role_labels(df, roles)
    plt.xticks(range(0, len(labels)), labels)
    ax.set_ylabel(measure_id)
    plt.tight_layout()


def draw_categorical_violin_distribution(
        df, measure_id, ax=None, numerical_categories=False):
    if ax is None:
        ax = plt.gca()

    df = df.copy()
    if df.empty:
        return

    color_male, color_female = male_female_colors()

    numerical_measure_name = measure_id + "_numerical"
    if not numerical_categories:
        df[numerical_measure_name], values_domain = \
            _enumerate_by_count(df, measure_id)
    else:
        df[numerical_measure_name], values_domain = \
            _enumerate_by_natural_order(df, measure_id)
    y_locations = np.arange(len(values_domain))

    bin_edges = y_locations - 0.5
    centers = bin_edges
    heights = 0.8

    hist_range = (np.min(y_locations), np.max(y_locations))

    datasets = []
    binned_datasets = []
    roles = roles_to_draw(df)

    for role in roles:
        df_role = df[df.role == role]

        df_male = df_role[df_role.gender == 'M']
        df_female = df_role[df_role.gender == 'F']

        male_data = df_male[numerical_measure_name].values
        female_data = df_female[numerical_measure_name].values
        datasets.append((male_data, female_data))

        binned_datasets.append([
            np.histogram(d, range=hist_range, bins=len(y_locations))[0]
            for d in [male_data, female_data]
        ])

    binned_maximum = np.max(
        [np.max([np.max(m), np.max(f)]) for (m, f) in binned_datasets]
    )

    x_locations = np.arange(
        0, len(roles) * 2 * binned_maximum, 2 * binned_maximum)

    _fig, ax = plt.subplots()
    _fig.set_size_inches(2 + len(roles), 8)
    for count, (male, female) in enumerate(binned_datasets):
        x_loc = x_locations[count]

        lefts = x_loc - male
        ax.barh(centers, male, height=heights, left=lefts, color=color_male)
        ax.barh(centers, female, height=heights,
                left=x_loc, color=color_female)

    ax.set_yticks(y_locations)
    ax.set_yticklabels(map(lambda x: textwrap.fill(x, 20), values_domain))
    ax.set_xlim(2 * -binned_maximum, len(roles) * 2 * binned_maximum)
    ax.set_ylim(-1, np.max(y_locations) + 1)

    ax.set_ylabel(measure_id)
    ax.set_xlabel('role')
    labels = role_labels(df, roles)
    plt.xticks(x_locations, labels)

    male_female_legend(color_male, color_female, ax)

    plt.tight_layout()


def draw_ordinal_violin_distribution(df, measure_id, ax=None):
    df[measure_id] = df[measure_id].apply(lambda x: str(x))
    draw_categorical_violin_distribution(
        df, measure_id, numerical_categories=True)
