'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function, absolute_import, unicode_literals

from __future__ import division
from past.utils import old_div
import numpy as np
from .annotate_composite import AnnotatorBase
from .raw_vcf import samples_to_alleles_index


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

    def get_vcf_variant(self, allele):
        return self.family_variants.vcf.vars[allele['summary_variant_index']]

    def get_variant_full_genotype(self, allele):
        vcf_variant = self.get_vcf_variant(allele)
        gt = vcf_variant.gt_idxs[
            samples_to_alleles_index(self.independent_index)]
        gt = gt.reshape([2, len(self.independent_index)], order='F')
        unknown = np.any(gt == -1, axis=0)
        gt = gt[:, np.logical_not(unknown)]

        return gt

    def annotate_variant_allele(self, allele):
        n_independent_parents = self.n_independent_parents

        gt = self.get_variant_full_genotype(allele)

        n_parents_called = gt.shape[1]
        percent_parents_called = old_div((
            100.0 * n_parents_called), n_independent_parents)

        allele_index = allele['allele_index']
        n_alleles = np.sum(gt == allele_index)
        allele_freq = 0.0
        if n_parents_called > 0:
            allele_freq = old_div(
                (100.0 * n_alleles), (2.0 * n_parents_called))

        return n_parents_called, percent_parents_called, \
            n_alleles, allele_freq
