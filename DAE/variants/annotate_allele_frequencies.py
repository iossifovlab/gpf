'''
Created on Mar 5, 2018

@author: lubo
'''
import numpy as np
from variants.annotate_composite import AnnotatorBase
from variants.raw_vcf import samples_to_alleles_index


class VcfAlleleFrequencyAnnotator(AnnotatorBase):
    COLUMNS = [
        'af_parents_called_count',
        'af_parents_called_percent',
        'af_allele_count',
        'af_allele_freq',
    ]

    def __init__(self):
        super(VcfAlleleFrequencyAnnotator, self).__init__()
        self.family_variants = None
        self.independent = None
        self.independent_index = None
        self.n_independent_parents = None

    def setup(self, family_variants):
        super(VcfAlleleFrequencyAnnotator, self).setup(family_variants)

        self.family_variants = family_variants

        self.independent = self.family_variants.persons_without_parents()
        self.independent_index = \
            np.array(self.family_variants.persons_samples(self.independent))

        self.n_independent_parents = len(self.independent)

    def annotate_variant(self, vcf_variant):
        n_independent_parents = self.n_independent_parents

        gt = vcf_variant.gt_idxs[
            samples_to_alleles_index(self.independent_index)]
        gt = gt.reshape([2, len(self.independent_index)], order='F')

        unknown = np.any(gt == -1, axis=0)
        gt = gt[:, np.logical_not(unknown)]

        n_parents_called = gt.shape[1]
        percent_parents_called = (
            100.0 * n_parents_called) / n_independent_parents

        n_ref_alleles = np.sum(gt == 0)
        ref_freq = 0.0
        if n_parents_called > 0:
            ref_freq = (100.0 * n_ref_alleles) / (2.0 * n_parents_called)
        alleles_frequencies = [ref_freq]
        alleles_counts = [n_ref_alleles]

        for alt_allele in range(len(vcf_variant.ALT)):
            n_alt_allele = np.sum(gt == alt_allele + 1)
            if n_parents_called == 0:
                alt_allele_freq = 0
            else:
                alt_allele_freq = \
                    (100.0 * n_alt_allele) / (2.0 * n_parents_called)
            alleles_counts.append(n_alt_allele)
            alleles_frequencies.append(alt_allele_freq)

        assert n_parents_called * 2 == sum(alleles_counts)
        size = len(vcf_variant.ALT) + 1
        return (n_parents_called * np.ones(size, np.int32),
                percent_parents_called * np.ones(size, np.float64),
                np.array(alleles_counts),
                np.array(alleles_frequencies, dtype=np.float64))

#     def annotate(self, vars_df, vcf_vars):
#         n_parents_called = pd.Series(index=vars_df.index, dtype=np.int16)
#         n_ref_alleles = pd.Series(index=vars_df.index, dtype=np.int16)
#         percent_parents_called = pd.Series(
#             index=vars_df.index, dtype=np.float32)
#
#         n_alt_alleles = pd.Series(index=vars_df.index, dtype=np.object_)
#         alt_alleles_freq = pd.Series(index=vars_df.index, dtype=np.object_)
#
#         for index, v in enumerate(vcf_vars):
#             res = self.annotate_variant(v)
#             n_parents_called[index], percent_parents_called[index], \
#                 n_alt_alleles[index], alt_alleles_freq[index], \
#                 n_ref_alleles[index] = res
#
#         vars_df['all.nParCalled'] = n_parents_called
#         vars_df['all.prcntParCalled'] = percent_parents_called
#         vars_df['all.nAltAlls'] = n_alt_alleles
#         vars_df['all.nRefAlls'] = n_ref_alleles
#         vars_df['all.altFreq'] = alt_alleles_freq
#
#         return vars_df
