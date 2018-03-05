'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.raw_vcf import VcfFamily
from variants.variant import mat2str


class AlleleCounter(object):

    def __init__(self, family_variants):
        super(AlleleCounter, self).__init__()
        self.family_variants = family_variants

        self.independent = self.family_variants.persons_without_parents()
        self.independent_index = \
            np.array(self.family_variants.persons_index(self.independent))
        self.parents = len(self.independent)

    def count_alt_allele(self, vcf):
        assert self.independent
        assert self.independent_index is not None

        gt = vcf.gt_idxs[
            VcfFamily.samples_to_alleles_index(self.independent_index)]
        gt = gt.reshape([2, len(self.independent_index)], order='F')

        unknown = np.any(gt == -1, axis=0)
        gt = gt[:, np.logical_not(unknown)]

        n_parents_called = gt.shape[1]

        result = {
            'gt': mat2str(gt),
            'n_parents_called': n_parents_called,
            'percent_parents_called': (100.0 * n_parents_called) / self.parents
        }
        for alt_allele, alt in enumerate(vcf.ALT):
            n_alt_allele = np.sum(gt == alt_allele + 1)
            result[alt] = {
                'n_alt_allele': n_alt_allele,
                'alt_allele_freq':
                (100.0 * n_alt_allele) / 2.0 * n_parents_called
            }
        return result
