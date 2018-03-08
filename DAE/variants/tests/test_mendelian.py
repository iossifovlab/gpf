'''
Created on Feb 14, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
import numpy as np
from variants.vcf_utils import mat2str


def test_mendelian(ustudy):
    variants = ustudy.query_variants(
        family_id=['AU1921'], regions=[Region("1", 11541, 54721)])

    for v in variants:
        print(v, v.is_mendelian(), v.effect_type)
        print(mat2str(v.best_st))
        print(mat2str(v.gt))


def test_mendelian_trio_1(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [0, 0, 0]])
    assert not v.is_mendelian()
    assert v.is_reference()


def test_non_mendelian_trio_1(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 1],
                     [0, 0, 0]])
    assert not v.is_mendelian()


def test_non_mendelian_trio_2(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [0, 0, 1]])
    assert not v.is_mendelian()


def test_mendelian_trio_2(fv1):
    v = fv1.clone()
    v.gt = np.array([[1, 0, 0],
                     [0, 0, 1]])
    assert v.is_mendelian()


def test_mendelian_trio_3(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [1, 0, 1]])
    assert v.is_mendelian()


def test_mendelian_trio_4(fv1):
    v = fv1.clone()
    v.gt = np.array([[1, 0, 0],
                     [1, 0, 1]])
    assert v.is_mendelian()


def test_mendelian_trio_5(fv1):
    v = fv1.clone()
    v.gt = np.array([[1, 1, 0],
                     [1, 0, 1]])
    assert v.is_mendelian()


def test_mendelian_trio_6(fv1):
    v = fv1.clone()
    v.gt = np.array([[1, 1, 1],
                     [1, 0, 1]])
    assert v.is_mendelian()


def test_mendelian_quad_1(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 0, 0, 0],
                     [0, 0, 0, 0]])
    assert not v.is_mendelian()
    assert v.is_reference()


def test_mendelian_quad_2(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 1, 0, 0],
                     [0, 0, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_quad_3(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 0],
                     [0, 0, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_quad_4(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [0, 0, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_quad_5(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [0, 0, 1, 1]])
    assert v.is_mendelian()


def test_mendelian_quad_6(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [1, 1, 1, 1]])
    assert v.is_mendelian()


def test_mendelian_quad_7(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [0, 0, 1, 1]])
    assert v.is_mendelian()


def test_non_mendelian_quad_1(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 1],
                     [0, 1, 1, 1]])
    assert not v.is_mendelian()


def test_non_mendelian_quad_2(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 1],
                     [0, 1, 0, 1]])
    assert not v.is_mendelian()


def test_mendelian_quad_8(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 1],
                     [0, 1, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_quad_9(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 0],
                     [0, 1, 0, 1]])
    assert v.is_mendelian()


def test_mendelian_multi_1(fv3):
    v = fv3.clone()
    v.gt = np.array([[0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0]])
    assert not v.is_mendelian()
    assert v.is_reference()


def test_mendelian_multi_2(fv3):
    v = fv3.clone()
    v.gt = np.array([[1, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_multi_3(fv3):
    v = fv3.clone()
    v.gt = np.array([[1, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0]])
    assert not v.is_mendelian()


def test_mendelian_multi_4(fv3):
    v = fv3.clone()
    v.gt = np.array([[1, 0, 1, 0, 0],
                     [1, 0, 0, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_multi_5(fv3):
    v = fv3.clone()
    v.gt = np.array([[1, 1, 1, 0, 0],
                     [1, 0, 0, 0, 0]])
    assert v.is_mendelian()


def test_mendelian_multi_6(fv3):
    v = fv3.clone()
    v.gt = np.array([[1, 1, 1, 0, 0],
                     [1, 0, 1, 0, 0]])
    assert not v.is_mendelian()


def test_mendelian_multi_7(fv3):
    v = fv3.clone()
    v.gt = np.array([[1, 1, 1, 0, 1],
                     [1, 0, 1, 0, 0]])
    assert v.is_mendelian()
