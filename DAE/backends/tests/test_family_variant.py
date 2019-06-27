'''
Created on Jul 9, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

import numpy as np
from utils.vcf_utils import mat2str


@pytest.mark.parametrize("gt,bs", [
    (np.array([[0, 0, 1], [0, 0, 2]], dtype='int8'), "220/001/001"),
    (np.array([[0, 0, 1], [0, 0, 0]], dtype='int8'), "221/001/000"),
    (np.array([[0, 0, 0], [0, 0, 2]], dtype='int8'), "221/000/001"),
    (np.array([[0, 0, 0], [0, 0, 0]], dtype='int8'), "222/000/000"),
])
def test_family_variant_best_st(fv1, gt, bs):
    v = fv1(gt)
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == bs


@pytest.mark.parametrize("gt,bs", [
    (np.array([[-1, 0, 1], [0, 0, 2]], dtype='int8'), "?20/?01/?01"),
    (np.array([[-1, 0, 1], [0, 0, 0]], dtype='int8'), "?21/?01/?00"),
    (np.array([[-1, 0, 0], [0, 0, 2]], dtype='int8'), "?21/?00/?01"),
    (np.array([[-1, 0, 0], [0, 0, 0]], dtype='int8'), "?22/?00/?00"),
])
def test_family_variant_unknown_best_st(fv1, gt, bs):
    v = fv1(gt)
    print(v)
    print(mat2str(v.best_st))
    assert mat2str(v.best_st) == bs
