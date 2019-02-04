'''
Created on Nov 9, 2016

@author: lubo
'''
from __future__ import unicode_literals

from builtins import object
from collections import Counter

from scipy.stats.stats import ttest_ind

# from VariantsDB import Person
import numpy as np
import pandas as pd
from pheno_tool.genotype_helper import GenotypeHelper
from pheno_tool.genotype_helper import VariantsType as VT

from pheno_tool.pheno_common import PhenoFilterBuilder, PhenoResult
import statsmodels.api as sm
from pheno.common import Role, Gender
import logging

# from utils.profiler import profile
LOGGER = logging.getLogger(__name__)


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

    # @profile("pheno_tool_init.prof")
    def __init__(self, phdb, studies, roles,
                 measure_id, normalize_by=[],
                 pheno_filters={}):

        assert phdb.has_measure(measure_id)
        assert all([phdb.has_measure(m) for m in normalize_by])

        assert len(roles) >= 1
        assert all([isinstance(r, Role) for r in roles])

        self.phdb = phdb
        self.studies = studies
        self.roles = roles

        self.persons = None
        self.measure_id = measure_id
        self.normalize_by = normalize_by
        self.genotype_helper = GenotypeHelper(studies)

        filter_builder = PhenoFilterBuilder(phdb)

        self.pheno_filters = [
            filter_builder.make_filter(m, c) for m, c in list(pheno_filters.items())
        ]
        self._build_subjects()
        self._normalize_df(self.df, self.measure_id, self.normalize_by)

    @classmethod
    def _assert_persons_equal(cls, p1, p2):
        if p1.personId == p2.personId and \
                p1.role == p2.role and \
                p1.gender == p2.gender:

            return True
        else:
            LOGGER.info("mismatched persons: {} != {}".format(p1, p2))
            return False

    @classmethod
    def _studies_persons(cls, studies, roles):
        persons = {}
        for st in studies:
            for fam in list(st.families.values()):
                for person in fam.memberInOrder:
                    if person.role in roles and \
                            person.personId not in persons:
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
        assert all([self.phdb.get_measure(m).measure_type == 'continuous' for m in normalize_by])
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
        if len(data) == 0:
            result = PhenoResult(None, None)
            result.positive_count = np.nan
            result.positive_mean = np.nan
            result.positive_deviation = np.nan

            result.negative_count = np.nan
            result.negative_mean = np.nan
            result.negative_deviation = np.nan
            return result

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

    # @profile("pheno_tool_calc.prof")
    def calc(self, variants, gender_split=False):
        """
        `variants` -- expects either variants type specification (instance of
        :ref:`VariantsType` class) or already calculated variants from
        :ref:`GenotypeHelper` class.

        `gender_split` -- should we split the result by gender or not. Default
        is `False`.

        """
        if isinstance(variants, VT):
            persons_variants = self.genotype_helper.get_persons_variants_df(
                variants)
        elif isinstance(variants, Counter):

            persons_variants = pd.DataFrame(
                data=[(k, v) for k, v in list(variants.items())],
                columns=['person_id', 'variants'])
            persons_variants.set_index('person_id', inplace=True)
        elif isinstance(variants, pd.DataFrame):
            persons_variants = variants
        else:
            raise ValueError(
                "expected VariantsType object or persons variants")

        if 'variants' in self.df:
            # delete variants column
            del self.df['variants']

        df = self.df.join(
            persons_variants, on="person_id", rsuffix="_variants")
        df.fillna(0, inplace=True)

        if not gender_split:
            return self._calc_stats(df, None)
        else:
            result = {}
            for gender in [Gender.M, Gender.F]:
                p = self._calc_stats(df, gender)
                result[gender.name] = p
            return result
