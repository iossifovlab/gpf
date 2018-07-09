'''
Created on Jul 9, 2018

@author: lubo
'''
from __future__ import print_function
import numpy as np
from variants.family_variant import FamilyVariant
from variants.vcf_utils import mat2str


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


def test_family_variant_best_st(fv1):
    v = fv1(
        np.array([[0, 0, 1],
                  [0, 0, 2]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "220/001/001"

    v = fv1(
        np.array([[0, 0, 1],
                  [0, 0, 0]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "221/001/000"

    v = fv1(
        np.array([[0, 0, 0],
                  [0, 0, 2]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "221/000/001"

    v = fv1(
        np.array([[0, 0, 0],
                  [0, 0, 0]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "222/000/000"


def test_family_variant_unknown_best_st(fv1):
    v = fv1(
        np.array([[-1, 0, 1],
                  [0, 0, 2]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "?20/?01/?01"

    v = fv1(
        np.array([[-1, 0, 1],
                  [0, 0, 0]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "?21/?01/?00"

    v = fv1(
        np.array([[-1, 0, 0],
                  [0, 0, 2]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "?21/?00/?01"

    v = fv1(
        np.array([[-1, 0, 0],
                  [0, 0, 0]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "?22/?00/?00"


def test_family_allele_best_st(fv1):
    v = fv1(
        np.array([[0, 0, 1],
                  [0, 0, 2]])
    )
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == "220/001/001"

    fa0 = v.alt_alleles[0]
    fa1 = v.alt_alleles[1]

