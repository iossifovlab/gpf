'''
Created on Mar 5, 2018

@author: lubo
'''
import numpy as np
import pandas as pd

from variants.family import FamiliesBase
from variants.vcf_utils import VcfFamily
from variants.vcf_utils import samples_to_alleles_index, mat2str


class VcfAlleleFrequency(object):

    def __init__(self, family_variants):
        super(VcfAlleleFrequency, self).__init__()
        self.family_variants = family_variants

        self.independent = self.family_variants.persons_without_parents()
        self.independent_index = \
            np.array(self.family_variants.persons_index(self.independent))

        self.parents = len(self.independent)

    @staticmethod
    def count_alt_allele(vcf_var, independent_samples):
        n_independent_parents = len(independent_samples)

        gt = vcf_var.gt_idxs[
            samples_to_alleles_index(independent_samples)]
        gt = gt.reshape([2, len(independent_samples)], order='F')

        unknown = np.any(gt == -1, axis=0)
        gt = gt[:, np.logical_not(unknown)]

        n_parents_called = gt.shape[1]
        result = {
            'gt': mat2str(gt),
            'n_parents_called': n_parents_called,
            'percent_parents_called':
            (100.0 * n_parents_called) / n_independent_parents
        }
        alleles_frequencies = []
        alleles_counts = []

        n_ref_alleles = np.sum(gt == 0)

        for alt_allele, alt in enumerate(vcf_var.ALT):
            n_alt_allele = np.sum(gt == alt_allele + 1)
            if n_parents_called == 0:
                # print(vcf.start, mat2str(gt), n_parents_called, n_alt_allele)
                alt_allele_freq = 0
            else:
                alt_allele_freq = \
                    (100.0 * n_alt_allele) / (2.0 * n_parents_called)
            alleles_counts.append(n_alt_allele)
            alleles_frequencies.append(alt_allele_freq)

            result[alt] = {
                'n_alt_allele': n_alt_allele,
                'alt_allele_freq': alt_allele_freq,
            }
        result['n_alt_alleles'] = np.array(alleles_counts)
        result['alt_alleles_freq'] = np.array(alleles_frequencies)
        result['n_ref_alleles'] = np.array(n_ref_alleles)

        assert n_parents_called * 2 == sum(alleles_counts) + n_ref_alleles
        return result

    def calc_allele_frequencies(self, vars_df, vcf_vars):
        n_parents_called = pd.Series(index=vars_df.index, dtype=np.int16)
        n_ref_alleles = pd.Series(index=vars_df.index, dtype=np.int16)
        percent_parents_called = pd.Series(
            index=vars_df.index, dtype=np.float32)

        n_alt_alleles = pd.Series(index=vars_df.index, dtype=np.object_)
        alt_alleles_freq = pd.Series(index=vars_df.index, dtype=np.object_)

        for index, v in enumerate(vcf_vars):
            res = self.count_alt_allele(v, self.independent_index)
            n_parents_called[index] = res['n_parents_called']
            n_ref_alleles[index] = res['n_ref_alleles']
            percent_parents_called[index] = res['percent_parents_called']
            n_alt_alleles[index] = res['n_alt_alleles']
            alt_alleles_freq[index] = res['alt_alleles_freq']

        vars_df['n_parents_called'] = n_parents_called
        vars_df['percent_parents_called'] = percent_parents_called
        vars_df['n_alt_alleles'] = n_alt_alleles
        vars_df['n_ref_alleles'] = n_ref_alleles
        vars_df['alt_allele_freq'] = alt_alleles_freq
        print(vars_df.head())

        return vars_df


class AlleleFrequencyAnnotator(FamiliesBase):

    def __init__(self, ped_df, vcf, vars_df):
        super(AlleleFrequencyAnnotator, self).__init__()

        self.ped_df = ped_df
        self.vcf = vcf
        self.vcf_vars = vcf.vars
        self.vars_df = vars_df

        self.families_build(ped_df, family_class=VcfFamily)

    def annotate(self):
        print(self.vars_df.head())

        allele_counter = VcfAlleleFrequency(self)
        vars_df = allele_counter.calc_allele_frequencies(
            self.vars_df, self.vcf_vars)
        print(vars_df.head())

        return vars_df
