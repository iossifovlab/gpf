'''
Created on Nov 9, 2016

@author: lubo
'''
from __future__ import unicode_literals

from builtins import object
from collections import Counter

import logging
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats.stats import ttest_ind

from pheno_tool.pheno_common import PhenoFilterBuilder, PhenoResult
from pheno.common import MeasureType
from variants.attributes import Role, Sex


LOGGER = logging.getLogger(__name__)


class PhenoToolHelper(object):
    """
    Helper class for PhenoTool. Collects variants and person ids from a study.

    Arguments of the constructor are:

    `study` -- an instance of StudyWrapper or DatasetWrapper
    """

    LGD_EFFECTS = ['splice-site', 'frame-shift',
                   'nonsense', 'no-frame-shift-newStop']

    def __init__(self, study):
        self.study = study

    def study_persons(self, roles=[Role.prb]):
        assert isinstance(roles, list)
        persons = list()
        for family in self.study.families.values():
            for person in family.members_in_order:
                if person.role in roles and person.person_id not in persons:
                    persons.append(person.person_id)
        return persons

    def study_variants(self, data):
        variants_by_effect = {}
        lgds = 'LGDs' in data['effectTypes']

        if lgds:
            oldeffecttypes = list(data['effectTypes'])
            data['effectTypes'].pop(data['effectTypes'].index('LGDs'))
            data['effectTypes'].extend(self.LGD_EFFECTS)

        for variant in self.study.query_variants(**data):
            for allele in variant.matched_alleles:
                if allele.effect.worst not in variants_by_effect:
                    variants_by_effect[allele.effect.worst] = Counter()
                for person in allele.variant_in_members:
                    if person:
                        variants_by_effect[allele.effect.worst][person] = 1

        if lgds:
            data['effectTypes'] = oldeffecttypes
            variants_by_effect['lgds'] = Counter()
            for lgd_effect in self.LGD_EFFECTS:
                if lgd_effect in variants_by_effect:
                    variants_by_effect['lgds'] += \
                        variants_by_effect[lgd_effect]
                    del(variants_by_effect[lgd_effect])

        return variants_by_effect


class PhenoTool(object):
    """
    Tool to estimate dependency between variants and phenotype measrues.

    Arguments of the constructor are:

    `pheno_db` -- an instance of PhenoDB

    `measure_id` -- a phenotype measure ID

    `_person_ids` -- an optional list of person IDs to filter the phenotype
    database with

    `normalize_by` -- list of continuous measure names. Default value is
    an empty list

    `pheno_filters` -- dictionary of measure IDs and filter specifiers. Default
    is empty dictionary.
    """

    def __init__(self, pheno_db, measure_id, _person_ids=[],
                 normalize_by=[], pheno_filters=[]):

        self.pheno_db = pheno_db
        self.measure_id = measure_id

        assert isinstance(pheno_filters, list)
        assert self.pheno_db.has_measure(measure_id)
        assert self.pheno_db.get_measure(self.measure_id).measure_type in \
            [MeasureType.continuous, MeasureType.ordinal]

        self.normalize_by = self._init_normalize_measures(normalize_by)
        self.pheno_filters = \
            pheno_filters and self._init_pheno_filters(pheno_filters)

        # TODO currently filtering only for probands, expand with additional
        # options via PeopleGroup
        all_measures = [self.measure_id] + self.normalize_by

        pheno_df = self.pheno_db.get_persons_values_df(
            all_measures, person_ids=_person_ids, roles=[Role.prb])
        self.pheno_df = pheno_df.dropna()

        for f in self.pheno_filters:
            self.pheno_df = f.apply(self.pheno_df)
        self.pheno_df = self._normalize_df(self.pheno_df, self.measure_id,
                                           self.normalize_by)

    def _init_pheno_filters(self, pheno_filters):
        filter_builder = PhenoFilterBuilder(self.pheno_db)
        return [filter_builder.make_filter(m, c)
                for m, c in list(pheno_filters.items())]

    def _init_normalize_measures(self, normalize_by):
        normalize_by = [self._get_normalize_measure_id(normalize_measure)
                        for normalize_measure in normalize_by]
        normalize_by = list(filter(None, normalize_by))

        assert all([self.pheno_db.get_measure(m).measure_type
                    == MeasureType.continuous
                    for m in normalize_by])
        return normalize_by

    def _get_normalize_measure_id(self, normalize_measure):
        if not normalize_measure['instrument_name']:
            normalize_measure['instrument_name'] = \
                self.measure_id.split('.')[0]

        normalize_id = '.'.join([normalize_measure['instrument_name'],
                                 normalize_measure['measure_name']])
        if self.pheno_db.has_measure(normalize_id):
            return normalize_id
        else:
            return None

    @staticmethod
    def join_pheno_df_with_variants(pheno_df, variants):
        assert(isinstance(variants, Counter))
        persons_variants = pd.DataFrame(
            data=list(variants.items()),
            columns=['person_id', 'variant_count'])
        persons_variants = persons_variants.set_index('person_id')

        merged_df = pd.merge(pheno_df, persons_variants,
                             how='left', on=['person_id'])
        merged_df = merged_df.fillna(0)
        return merged_df

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
    def _calc_stats(cls, data, sex):
        if len(data) == 0:
            result = PhenoResult(None, None)
            result.positive_count = 0
            result.positive_mean = 0
            result.positive_deviation = 0

            result.negative_count = 0
            result.negative_mean = 0
            result.negative_deviation = 0
            result.pvalue = 'NA'
            return result

        positive_index = np.logical_and(
            data['variant_count'] != 0, ~np.isnan(data['variant_count']))

        negative_index = data['variant_count'] == 0

        if sex is None:
            sex_index = None
            positive_sex_index = positive_index
            negative_sex_index = negative_index
        else:
            sex_index = data['sex'] == sex
            positive_sex_index = np.logical_and(
                positive_index, sex_index)
            negative_sex_index = np.logical_and(negative_index,
                                                sex_index)

            assert not np.any(np.logical_and(positive_sex_index,
                                             negative_sex_index))

        positive = data[positive_sex_index].normalized.values
        negative = data[negative_sex_index].normalized.values
        p_val = cls._calc_pv(positive, negative)

        result = PhenoResult(data, sex_index)
        result._set_positive_stats(*PhenoTool._calc_base_stats(positive))
        result._set_negative_stats(*PhenoTool._calc_base_stats(negative))
        result.pvalue = p_val

        return result

    def calc(self, variants, sex_split=False):
        """
        `variants` -- an instance of Counter, matching personIds to
        an amount of variants

        `sex_split` -- should we split the result by sex or not. Default
        is `False`.

        """
        merged_df = PhenoTool.join_pheno_df_with_variants(self.pheno_df,
                                                          variants)
        if not sex_split:
            return self._calc_stats(merged_df, None)
        else:
            result = {}
            for sex in [Sex.M, Sex.F]:
                p = self._calc_stats(merged_df, sex)
                result[sex.name] = p
            return result
