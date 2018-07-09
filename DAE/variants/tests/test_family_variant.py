'''
Created on Jul 9, 2018

@author: lubo
'''
from __future__ import print_function
import numpy as np
from variants.family_variant import FamilyVariant


def test_family_allele_genotype(fv1):
    gt = np.array([[0, 0, 1],
                   [0, 0, 2]])
    v = fv1(gt)
    print(v)

    print(FamilyVariant.get_allele_genotype(gt, 1))
    print(FamilyVariant.get_allele_genotype(gt, 2))

    assert np.all(np.array([[0, 0, 1], [0, 0, -1]]) ==
                  FamilyVariant.get_allele_genotype(gt, 1))
    assert np.all(np.array([[0, 0, -1], [0, 0, 2]]) ==
                  FamilyVariant.get_allele_genotype(gt, 2))
