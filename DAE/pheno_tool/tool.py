'''
Created on Nov 9, 2016

@author: lubo
'''

from scipy.stats.stats import ttest_ind

import numpy as np
import pandas as pd
import statsmodels.api as sm
from collections import Counter
from VariantsDB import Person
from pheno_tool.genotype_helper import GenotypeHelper


class PhenoFilter(object):

    def __init__(self, phdb, measure_id):
        assert phdb.has_measure(measure_id)

        self.phdb = phdb
        self.measure_id = measure_id


class PhenoFilterSet(PhenoFilter):

    def __init__(self, phdb, measure_id, values_set):
        super(PhenoFilterSet, self).__init__(phdb, measure_id)

        measure_type = phdb.get_measure(measure_id).measure_type
        assert measure_type == 'categorical'

        assert isinstance(values_set, list) or isinstance(values_set, set)
        self.value_set = values_set

    def apply(self, df):
        return df[df[self.measure_id].isin(self.value_set)]


class PhenoFilterRange(PhenoFilter):

    def __init__(self, phdb, measure_id, values_range):
        super(PhenoFilterRange, self).__init__(phdb, measure_id)

        measure_type = phdb.get_measure(measure_id).measure_type
        assert measure_type == 'continuous' or measure_type == 'ordinal'

        assert isinstance(values_range, list) or \
            isinstance(values_range, tuple)
        self.values_min, self.values_max = values_range

    def apply(self, df):
        if self.values_min is not None and self.values_max is not None:
            return df[np.logical_and(
                df[self.measure_id] >= self.values_min,
                df[self.measure_id] <= self.values_max
            )]
        elif self.values_min is not None:
            return df[df[self.measure_id] >= self.values_min]
        elif self.values_max is not None:
            return df[df[self.measure_id] <= self.values_max]
        else:
            return df[-np.isnan(df[self.measure_id])]


class PhenoFilterBuilder(object):

    def __init__(self, phdb):
        self.phdb = phdb

    def make_filter(self, measure_id, constrants):
        measure = self.phdb.get_measure(measure_id)
        assert measure is not None
        if measure.measure_type == 'categorical':
            return PhenoFilterSet(self.phdb, measure_id, constrants)
        else:
            return PhenoFilterRange(self.phdb, measure_id, constrants)


class PhenoResult(object):

    def __init__(self, df, index=None):
        self.df = df
        self.genotypes_df = self._select_genotype(df, index)
        self.phenotypes_df = self._select_phenotype(df, index)
        self.pvalue = None
        self.positive_count = None
        self.positive_mean = None
        self.positive_deviation = None
        self.negative_count = None
        self.negative_mean = None
        self.negative_deviation = None

    @staticmethod
    def _select_genotype(df, index):
        gdf = df[['person_id', 'gender', 'role', 'variants']]
        if index is not None:
            gdf = gdf[index]
        return gdf

    @staticmethod
    def _select_phenotype(df, index):
        columns = list(df.columns)
        del columns[columns.index('variants')]
        del columns[columns.index('family_id')]

        pdf = df[columns]
        if index is not None:
            pdf = pdf[index]
        return pdf

    def _set_positive_stats(self, p_count, p_mean, p_std):
        self.positive_count = p_count
        self.positive_mean = p_mean
        self.positive_deviation = p_std

    def _set_negative_stats(self, n_count, n_mean, n_std):
        self.negative_count = n_count
        self.negative_mean = n_mean
        self.negative_deviation = n_std

    @property
    def genotypes(self):
        result = Counter()
        for _index, row in self.genotypes_df.iterrows():
            result[row['person_id']] = row['variants']
        return result

    @property
    def phenotypes(self):
        result = {}
        for _index, row in self.phenotypes_df.iterrows():
            result[row['person_id']] = row.to_dict()
        return result

    def __repr__(self):
        return "PhenoResult: pvalue={:.3g}; pos={} (neg={})".format(
            self.pvalue, self.positive_count, self.negative_count)


class PhenoTool(object):
    """
    Tool to estimate dependency between variants and phenotype measrues.

    Arguments of the constructor are:
    'phdb' -- instance of `PhenoDB` class

    `studies` -- list of studies

    `roles` -- list of roles

    `measure_id` -- measure ID

    `normalize_by` -- list of continuous measures. Default value is an empty
    list

    `pheno_filters` -- dictionary of measure IDs and filter specifiers. Default
    is empty dictionary.
    """

    def __init__(self, phdb, studies, roles,
                 measure_id, normalize_by=[],
                 pheno_filters={}):

        assert phdb.has_measure(measure_id)
        assert all([phdb.has_measure(m) for m in normalize_by])

        assert len(roles) >= 1
        assert all([r in ['prb', 'sib', 'mom', 'dad'] for r in roles])

        self.phdb = phdb
        self.studies = studies
        self.roles = roles

        self.persons = None
        self.measure_id = measure_id
        self.normalize_by = normalize_by
        self.genotype_helper = GenotypeHelper(studies)

        filter_builder = PhenoFilterBuilder(phdb)

        self.pheno_filters = [
            filter_builder.make_filter(m, c) for m, c in pheno_filters.items()
        ]
        self._build_subjects()

    @classmethod
    def _assert_persons_equal(cls, p1, p2):
        if p1.personId == p2.personId and \
                p1.role == p2.role and \
                p1.gender == p2.gender:

            return True
        else:
            print("mismatched persons: {} != {}".format(p1, p2))
            return False

    @classmethod
    def _studies_persons(cls, studies, roles):
        persons = {}
        for st in studies:
            for fam in st.families.values():
                for person in fam.memberInOrder:
                    if person.role in roles and person.personId not in persons:
                        persons[person.personId] = person
        return persons

    @classmethod
    def _measures_persons_df(cls, phdb, roles, measures, persons):
        df = phdb.get_persons_values_df(measures, roles=roles)
        df.dropna(inplace=True)

        df = df[df.person_id.isin(persons)]

        return df

    @classmethod
    def _persons(cls, df):
        persons = {}
        for _index, row in df.iterrows():
            person = Person()
            person.personId = row['person_id']
            person.gender = row['gender']
            person.role = row['role']
            persons[person.personId] = person
        return persons

    def _build_subjects(self):
        persons = self._studies_persons(self.studies, self.roles)
        measures = [self.measure_id]
        measures.extend(self.normalize_by)
        for f in self.pheno_filters:
            measures.append(f.measure_id)

        df = self._measures_persons_df(
            self.phdb, self.roles,
            measures,
            persons)

        for f in self.pheno_filters:
            df = f.apply(df)

        self.df = df.copy()
        self.persons = self._persons(df)

    def list_of_subjects(self, rebuild=False):
        if self.persons is None or rebuild:
            self._build_subjects()
        return self.persons

    def list_of_subjects_df(self, rebuild=False):
        if self.df is None or rebuild:
            self._build_subjects()
        return self.df

    @staticmethod
    def _normalize_df(df, measure_id, normalize_by=[]):
        if not normalize_by:
            dn = pd.Series(
                index=df.index, data=df[measure_id].values)
            df['normalized'] = dn
            return df
        else:
            X = sm.add_constant(df[normalize_by])
            y = df[measure_id]
            model = sm.OLS(y, X)
            fitted = model.fit()

            dn = pd.Series(index=df.index, data=fitted.resid)
            df['normalized'] = dn
            return df

    def normalize_measure_values_df(self, measure_id, normalize_by=[]):
        """
        Returns a data frame containing values for the `measure_id`.

        Values are normalized if the argument `normalize_by` is a non empty
        list of measure_ids.
        """
        assert isinstance(normalize_by, list)
        assert all(map(
            lambda m: self.phdb.get_measure(m).measure_type == 'continuous',
            normalize_by))
        assert self.phdb.get_measure(measure_id).measure_type == 'continuous'

        measures = normalize_by[:]
        measures.append(measure_id)

        df = self.phdb.get_persons_values_df(measures, roles=self.roles)
        df.dropna(inplace=True)
        return self._normalize_df(df, measure_id, normalize_by)

    @staticmethod
    def _calc_base_stats(arr):
        count = len(arr)
        if count == 0:
            mean = 0
            std = 0
        else:
            mean = np.mean(arr, dtype=np.float64)
            std = 1.96 * \
                np.std(arr, dtype=np.float64) / np.sqrt(count)
        return count, mean, std

    @staticmethod
    def _calc_pv(positive, negative):
        if len(positive) < 2 or len(negative) < 2:
            return 'NA'
        tt = ttest_ind(positive, negative)
        pv = tt[1]
        return pv

    @classmethod
    def _calc_stats(cls, data, gender):
        positive_index = np.logical_and(
            data['variants'] != 0, ~np.isnan(data['variants']))

        negative_index = data['variants'] == 0

        if gender is None:
            gender_index = None
            positive_gender_index = positive_index
            negative_gender_index = negative_index
        else:
            gender_index = data['gender'] == gender
            positive_gender_index = np.logical_and(
                positive_index, gender_index)
            negative_gender_index = np.logical_and(negative_index,
                                                   gender_index)

            assert not np.any(np.logical_and(positive_gender_index,
                                             negative_gender_index))

        positive = data[positive_gender_index].normalized.values
        negative = data[negative_gender_index].normalized.values
        p_val = cls._calc_pv(positive, negative)

        result = PhenoResult(data, gender_index)
        result._set_positive_stats(*PhenoTool._calc_base_stats(positive))
        result._set_negative_stats(*PhenoTool._calc_base_stats(negative))

        result.pvalue = p_val

        return result

    def calc(self, gender_split=False, **kwargs):
        """
        `gender_split` -- should we split the result by gender or not. Default
        is `False`.

        `effect_types` -- list of effect types

        `gene_syms` -- list of gene symbols

        `present_in_child` -- list of present in child specifiers
        ("autism only", "unaffected only", "autism and unaffected",
        "proband only", "sibling only", "proband and sibling", "neither").

        `present_in_parent` -- list of present in parent specifiers
        ("mother only", "father only", "mother and father", "neither")

        `rarity` -- one of `ultraRare`, `rare`, `interval`. Together with
        `ratiry_max` and `rarity_min` specifies the rarity of transmitted
        variants.

        `rarity_max` -- used when *rarity* is `rare` or `interval`.
        Specifies the upper boundary of the rarity (percents)

        `rarity_min` -- used when *rarity* is `interval`. Specifies the lower
        boundary of rarity (percents)
        """
        persons_variants = self.genotype_helper.get_persons_variants(**kwargs)

        df = self._normalize_df(self.df, self.measure_id, self.normalize_by)

        variants = pd.Series(0, index=df.index)
        df['variants'] = variants

        for index, row in df.iterrows():
            person_id = row['person_id']
            assert person_id in self.persons

            var_count = persons_variants.get(person_id, 0)
            df.loc[index, 'variants'] = var_count

        if not gender_split:
            return self._calc_stats(df, None)
        else:
            result = {}
            for gender in ['M', 'F']:
                p = self._calc_stats(df, gender)
                result[gender] = p
            return result
