'''
Created on Jul 1, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
from variants.variant import FamilyAllele


def test_family_allele(sv, fam1):
    gt = np.array([[1, 0, 0], [1, 0, 1]])

    fa = FamilyAllele(sv.alleles[0], fam1, gt)
    print(fa, type(fa))
    print(dir(fa))

    print(fa.is_reference_allele)
    print(fa.members_ids)
    print(fa.members_in_order)
    print(fa.genotype)
    print(fa.family_id)
    print(fa.gt_flatten())

    print(fa.inheritance)

    fa = FamilyAllele(sv.alleles[1], fam1, gt)
    print(fa, type(fa))
    print(dir(fa))

    print(fa.inheritance)
