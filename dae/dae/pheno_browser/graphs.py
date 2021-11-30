"""
Created on Apr 10, 2017

@author: lubo
"""
import textwrap
import matplotlib as mpl

mpl.use("PDF")  # noqa

from dae.variants.attributes import Status, Sex

import matplotlib.pyplot as plt

plt.ioff()  # noqa

import pandas as pd
import numpy as np
import seaborn as sns
from dae.pheno.utils.lin_regress_wrapper import LinearRegressionWrapper
from dae.pheno.common import ROLES_GRAPHS_DEFINITION

import traceback


MAX_CATEGORIES_COUNT = 12
ROLES_COUNT_CUTOFF = 7


class GraphColumn(object):
    def __init__(self, name, roles, status, df):
        self.name = name
        self.roles = roles
        self.status = status
        self.df = df

    def all_count(self):
        return self.df.shape[0]

    def males_count(self):
        return self.df[self.df.sex == Sex.male].shape[0]

    def females_count(self):
        return self.df[self.df.sex == Sex.female].shape[0]

    @property
    def label(self):
        return self.name + "\n" + self.status.name

    @staticmethod
    def build(df, role_name, role_subroles, status):
        roles = role_subroles
        default_name = ", ".join([role.name for role in roles])
        label = role_name if role_name != "" else default_name

        df_roles = df[df.role.isin(roles)]
        df_roles_status = df_roles[df_roles.status == status]

        return GraphColumn(label, roles, status, df_roles_status)


def names(col1, col2):
    name1 = col1.split(".")[-1]
    name2 = col2.split(".")[-1]
    return (name1, name2)


def male_female_colors():
    [color_male, color_female] = gender_palette()
    return color_male, color_female


def male_female_legend(color_male, color_female, ax=None):
    if ax is None:
        ax = plt.gca()

    import matplotlib.patches as mpatches

    male_patch = mpatches.Patch(color=color_male, label="M")
    female_patch = mpatches.Patch(color=color_female, label="F")
    ax.legend(handles=[male_patch, female_patch], title="Sex")


def draw_linregres(df, col1, col2, jitter=None, ax=None):
    if ax is None:
        ax = plt.gca()

    dd = df.dropna()

    dmale = dd[dd.sex == Sex.male]
    dfemale = dd[dd.sex == Sex.female]

    name1, name2 = names(col1, col2)
    ax.set_xlabel(name1)
    ax.set_ylabel(name2)

    try:
        x = dmale[col1]
        y = dmale[col2]
        res_male = LinearRegressionWrapper(x, y)
    except ValueError:
        traceback.print_exc()
        res_male = None

    try:
        x = dfemale[col1]
        y = dfemale[col2]
        res_female = LinearRegressionWrapper(x, y)
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

    color_male, color_female = gender_palette_light()
    ax.plot(
        dmale[col1] + jmale1,
        dmale[col2] + jmale2,
        ".",
        color=color_male,
        ms=4,
        label="male",
    )
    ax.plot(
        dfemale[col1] + jfemale1,
        dfemale[col2] + jfemale2,
        ".",
        color=color_female,
        ms=4,
        label="female",
    )
    color_male, color_female = gender_palette()
    if res_male:
        ax.plot(dmale[col1], res_male.predict(), color=color_male)
    if res_female:
        ax.plot(dfemale[col1], res_female.predict(), color=color_female)
    male_female_legend(color_male, color_female, ax)
    # plt.tight_layout()
    return res_male, res_female


def draw_distribution(df, measure_id, ax=None):
    if ax is None:
        ax = plt.gca()

    color_male, color_female = male_female_colors()
    ax.hist(
        [
            df[df.sex == Sex.female][measure_id],
            df[df.sex == Sex.male][measure_id],
        ],
        color=[color_female, color_male],
        stacked=True,
        bins=20,
        normed=False,
    )
    male_female_legend(color_male, color_female, ax)

    ax.set_xlabel(measure_id)
    ax.set_ylabel("count")
    # plt.tight_layout()


def column_counts(column):
    counts = {
        "column_name": textwrap.fill(column.name, 9),
        "column_status": "$\\it{" + column.status.name + "}$",
        "column_total": column.all_count(),
        "male_total": column.males_count(),
        "female_total": column.females_count(),
    }
    return counts


def role_labels(ordered_columns):
    return [
        "{column_name}\n{column_status}\n"
        "all:{column_total:>4d}\n"
        "M: {male_total:>4d}\n"
        "F: {female_total:>4d}".format(**column_counts(col))
        for col in ordered_columns
    ]


def gender_palette_light():
    palette = sns.diverging_palette(240, 10, s=80, l=77, n=2)  # noqa
    return palette


def gender_palette():
    palette = sns.diverging_palette(240, 10, s=80, l=50, n=2)  # noqa
    return palette


def set_figure_size(figure, x_count):
    scale = 3.0 / 4.0
    figure.set_size_inches((8 + x_count) * scale, 8 * scale)


def _enumerate_by_count(df, column_name):
    occurrence_counts = df[column_name].value_counts()
    occurrence_ordered = occurrence_counts.index.values.tolist()
    occurrences_map = {
        value: number for (number, value) in enumerate(occurrence_ordered)
    }

    return (
        df[column_name].apply(lambda x: occurrences_map[x]),
        occurrence_ordered,
    )


def _enumerate_by_natural_order(df, column_name):
    values_domain = df[column_name].unique()
    values_domain = sorted(values_domain, key=lambda x: float(x))
    values_map = {
        value: number for (number, value) in enumerate(values_domain)
    }

    result = df[column_name].apply(lambda x: values_map[x])
    return result, values_domain


def draw_measure_violinplot(
    df, measure_id, roles_definition=ROLES_GRAPHS_DEFINITION, ax=None
):
    if ax is None:
        ax = plt.gca()

    df = df.copy()
    fig = plt.gcf()

    palette = gender_palette()
    columns = get_columns_to_draw(roles_definition, df)

    if len(columns) == 0:
        return False

    column_dfs = []
    for column in columns:
        column_df = column.df
        column_df["column_name"] = column.label
        column_dfs.append(column_df)
    df_with_column_names = pd.concat(column_dfs)

    assert df.shape[1] == df_with_column_names.shape[1] - 1
    column_names = [column.label for column in columns]

    set_figure_size(fig, len(columns))

    sns.violinplot(
        data=df_with_column_names,
        x="column_name",
        y=measure_id,
        hue="sex",
        order=column_names,
        hue_order=[Sex.male, Sex.female],
        linewidth=1,
        split=True,
        scale="count",
        scale_hue=False,
        palette=palette,
        saturation=1,
    )

    palette = gender_palette_light()
    sns.stripplot(
        data=df_with_column_names,
        x="column_name",
        y=measure_id,
        hue="sex",
        order=column_names,
        hue_order=[Sex.male, Sex.female],
        jitter=0.025,
        size=2,
        palette=palette,
        linewidth=0.1,
    )

    labels = role_labels(columns)
    plt.xticks(list(range(0, len(labels))), labels)
    ax.set_ylabel(measure_id)
    ax.set_xlabel("role")
    # plt.tight_layout()

    return True


def get_columns_to_draw(roles, df):
    columns = []
    for role_name, role_subroles in roles.items():
        for status in [Status.affected, Status.unaffected]:
            columns.append(
                GraphColumn.build(df, role_name, role_subroles, status)
            )

    dfs = [
        column
        for column in columns
        if column.all_count() >= ROLES_COUNT_CUTOFF
    ]

    return dfs


def draw_categorical_violin_distribution(
    df,
    measure_id,
    roles_definition=ROLES_GRAPHS_DEFINITION,
    ax=None,
    numerical_categories=False,
    max_categories=MAX_CATEGORIES_COUNT,
):
    if ax is None:
        ax = plt.gca()

    if df.empty:
        return False

    df = df.copy()

    color_male, color_female = male_female_colors()

    numerical_measure_name = measure_id + "_numerical"
    if not numerical_categories:
        df[numerical_measure_name], values_domain = _enumerate_by_count(
            df, measure_id
        )
    else:
        (
            df[numerical_measure_name],
            values_domain,
        ) = _enumerate_by_natural_order(df, measure_id)
    values_domain = values_domain[:max_categories]
    y_locations = np.arange(len(values_domain))

    columns = get_columns_to_draw(roles_definition, df)
    if len(columns) == 0:
        return False

    bin_edges = y_locations
    centers = bin_edges
    heights = 0.8

    hist_range = (np.min(y_locations), np.max(y_locations))

    binned_datasets = []

    for column in columns:
        df_role = column.df

        df_male = df_role[df_role.sex == Sex.male]
        df_female = df_role[df_role.sex == Sex.female]

        male_data = df_male[numerical_measure_name].values
        female_data = df_female[numerical_measure_name].values

        binned_datasets.append(
            [
                np.histogram(d, range=hist_range, bins=len(y_locations))[0]
                for d in [male_data, female_data]
            ]
        )

    binned_maximum = np.max(
        [np.max([np.max(m), np.max(f)]) for (m, f) in binned_datasets]
    )

    x_locations = np.arange(
        0, len(columns) * 2 * binned_maximum, 2 * binned_maximum
    )

    _fig, ax = plt.subplots()
    _fig.set_tight_layout(True)
    set_figure_size(_fig, len(columns))
    female_text_offeset = binned_maximum * 0.05
    for count, (male, female) in enumerate(binned_datasets):
        x_loc = x_locations[count]

        lefts = x_loc - male
        ax.barh(centers, male, height=heights, left=lefts, color=color_male)
        ax.barh(
            centers, female, height=heights, left=x_loc, color=color_female
        )

        for y, (male_count, female_count) in enumerate(zip(male, female)):
            ax.text(
                x_loc - male_count,
                y,
                str(male_count),
                horizontalalignment="center",
                verticalalignment="bottom",
                rotation=90,
                rotation_mode="anchor",
            )
            ax.text(
                x_loc + female_count + female_text_offeset,
                y,
                str(female_count),
                horizontalalignment="center",
                verticalalignment="top",
                rotation=90,
                rotation_mode="anchor",
            )

    ax.set_yticks(y_locations)
    ax.set_yticklabels([textwrap.fill(x, 20) for x in values_domain])
    ax.set_xlim(2 * -binned_maximum, len(columns) * 2 * binned_maximum)
    ax.set_ylim(-1, np.max(y_locations) + 1)

    ax.set_ylabel(measure_id)
    ax.set_xlabel("role")
    labels = role_labels(columns)
    plt.xticks(x_locations, labels)

    male_female_legend(color_male, color_female, ax)
    return True


def draw_ordinal_violin_distribution(df, measure_id, ax=None):
    df = df.copy()
    df[measure_id] = df[measure_id].apply(lambda x: str(x))
    return draw_categorical_violin_distribution(
        df, measure_id, numerical_categories=True
    )
