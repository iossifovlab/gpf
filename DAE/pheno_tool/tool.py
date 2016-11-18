'''
Created on Nov 9, 2016

@author: lubo
'''

from scipy.stats.stats import ttest_ind

import numpy as np
import pandas as pd
import statsmodels.api as sm
from query_variants import dae_query_variants
import itertools
from collections import Counter
from Variant import variantInMembers


DEFAULT_STUDY = 'ALL SSC'
DEFAULT_TRANSMITTED = 'w1202s766e611'


class PhenoRequest(object):
    """
    Represents query filters for finding family variants.

    Constructor arguments are:

    `effect_types` -- list of effect types

    `rarity` -- one of `ultraRare`, `rare`, `interval`. Together with
    `ratiry_max` and `rarity_min` specifies the rarity of transmitted variants.

    `rarity_max` -- used when *rarity* is `rare` or `interval`. Specifies the
    the upper boundary of the rarity (percents)

    `rarity_min` -- used when *rarity* is `interval`. Specifies the lower
    boundary of rarity (percents)
    """

    def __init__(
        self,
        effect_types=None,
        gene_syms=None,
        rarity='ultraRare',
        rarity_max=None,
        rarity_min=None,
    ):

        self.effect_types = effect_types
        self.gene_syms = gene_syms
        self.rarity = rarity
        self.rarity_max = rarity_max
        self.rarity_min = rarity_min

    def _dae_query_request(self):
        data = {
            'geneSyms': self.gene_syms,
            'effectTypes': self.effect_types,
            'rarity': self.rarity,
            'popFrequencyMax': self.rarity_max,
            'popFrequencyMin': self.rarity_min,
        }
        return data


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

    Receives as argument an instance of PhenoDB class.
    """

    def __init__(self, phdb, studies, roles):
        self.phdb = phdb
        self.studies = studies

        self.denovo_studies = [st for st in studies if st.has_denovo]
        self.transmitted_studies = [st for st in studies if st.has_transmitted]

        self.roles = roles

    @property
    def _present_in_child(self):
        pic = set([])
        if 'prb' in self.roles:
            pic.add('autism only')
            pic.add('autism and unaffected')
        if 'sib' in self.roles:
            pic.add('unaffected only')
            pic.add('autism and unaffected')
        if not pic or 'mom' in self.roles or 'dad' in self.roles:
            pic.add('neither')
        return ','.join(pic)

    @property
    def _present_in_parent(self):
        pic = set([])
        if 'mom' in self.roles:
            pic.add('mother only')
            pic.add('mother and father')
        if 'dad' in self.roles:
            pic.add('father only')
            pic.add('mother and father')
        if not pic or 'prb' in self.roles or 'sib' in self.roles:
            pic.add('neither')
        return ','.join(pic)

    def get_variants(self, request):
        query = request._dae_query_request()
        query.update({
            'denovoStudies': self.denovo_studies,
            'transmittedStudies': self.transmitted_studies,
            'presentInChild': self._present_in_child,
            'presentInParent': self._present_in_parent,
        })
        vs = dae_query_variants(query)
        return itertools.chain(*vs)

    def get_persons_variants(self, pheno_request):
        vs = self.get_variants(pheno_request)
        seen = set([])
        result = Counter()
        for v in vs:
            persons = variantInMembers(v)
            for p in persons:
                vid = "{}:{}:{}".format(p, v.location, v.variant)
                if vid not in seen:
                    seen.add(vid)
                    result[p] += 1
                else:
                    print("skipping {}".format(vid))
        return result

    def get_families_variants(self, pheno_request):
        vs = self.get_variants(pheno_request)
        seen = set([])
        result = Counter()
        for v in vs:
            vid = "{}:{}:{}".format(v.familyId, v.location, v.variant)
            if vid not in seen:
                seen.add(vid)
                result[v.familyId] += 1
        return result

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

        df = self.phdb.get_persons_values_df(measures, role='prb')
        df.dropna(inplace=True)

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

    def calc(self, pheno_request, measure_id, normalize_by=[],
             gender_split=False):
        df = self.normalize_measure_values_df(measure_id, normalize_by)
        persons_variants = self.get_persons_variants(pheno_request)

        variants = pd.Series(0, index=df.index)
        df['variants'] = variants

        for index, row in df.iterrows():
            person_id = row['person_id']
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
