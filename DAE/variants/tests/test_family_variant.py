'''
Created on Jul 9, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

import numpy as np
from variants.vcf_utils import mat2str


@pytest.mark.parametrize("gt,bs", [
    (np.array([[0, 0, 1], [0, 0, 2]]), "220/001/001"),
    (np.array([[0, 0, 1], [0, 0, 0]]), "221/001/000"),
    (np.array([[0, 0, 0], [0, 0, 2]]), "221/000/001"),
    (np.array([[0, 0, 0], [0, 0, 0]]), "222/000/000"),
])
def test_family_variant_best_st(fv1, gt, bs):
    v = fv1(gt)
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == bs


@pytest.mark.parametrize("gt,bs", [
    (np.array([[-1, 0, 1], [0, 0, 2]]), "?20/?01/?01"),
    (np.array([[-1, 0, 1], [0, 0, 0]]), "?21/?01/?00"),
    (np.array([[-1, 0, 0], [0, 0, 2]]), "?21/?00/?01"),
    (np.array([[-1, 0, 0], [0, 0, 0]]), "?22/?00/?00"),
])
def test_family_variant_unknown_best_st(fv1, gt, bs):
    v = fv1(gt)
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == bs


@pytest.mark.xfail
@pytest.mark.parametrize("gt,bs0,bs1", [
    (np.array([[0, 0, 1], [0, 0, 2]]), "221/001", "221/001"),
    (np.array([[0, 0, 1], [0, 0, 0]]), "221/001", None),
    (np.array([[0, 0, 2], [0, 0, 0]]), "221/001", None),
    (np.array([[0, 0, 0], [0, 0, 0]]), None, None)
])
def test_family_multi_allele_best_st(fv1, gt, bs0, bs1):
    v = fv1(gt)

    if bs0:
        fa0 = v.alt_alleles[0]
        print(fa0, mat2str(fa0.best_st))
        assert mat2str(fa0.best_st) == bs0

    if bs1:
        fa1 = v.alt_alleles[1]
        print(fa1, mat2str(fa1.best_st))
        assert mat2str(fa1.best_st) == bs1
