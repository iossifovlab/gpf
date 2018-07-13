'''
Created on Feb 27, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np
import pytest


pytestmark = pytest.mark.xfail()


def test_denovo_trio_1(fv1):
    gt = np.array([[0, 0, 1],
                   [0, 0, 0]])
    v = fv1(gt)
    print(v, type(v))

    assert not v.is_mendelian()
    assert v.is_denovo()


def test_denovo_trio_2(fv1):
    gt = np.array([[0, 0, 1],
                   [0, 0, 1]])
    v = fv1(gt)
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_denovo_trio_3(fv1):
    gt = np.array([[0, 0, 0],
                   [0, 0, 1]])
    v = fv1(gt)
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_not_denovo_trio_1(fv1):
    gt = np.array([[0, 0, 0],
                   [0, 0, 0]])
    v = fv1(gt)
    assert v.is_reference()
    assert not v.is_mendelian()
    assert not v.is_denovo()
    assert not v.is_omission()


def test_not_denovo_trio_2(fv1):
    gt = np.array([[0, 1, 0],
                   [0, 1, 0]])
    v = fv1(gt)
    assert not v.is_mendelian()
    assert not v.is_denovo()
    assert v.is_omission()


def test_not_denovo_trio_3(fv1):
    gt = np.array([[1, 1, 0],
                   [1, 1, 1]])
    v = fv1(gt)
    assert not v.is_mendelian()

    assert v.is_denovo()
    assert not v.is_omission()


def test_denovo_quad_1(fv2):
    gt = np.array([[0, 0, 1, 0],
                   [0, 0, 0, 0]])
    v = fv2(gt)
    assert not v.is_mendelian()
    assert v.is_denovo()
    assert not v.is_omission()


def test_denovo_quad_2(fv2):
    gt = np.array([[0, 0, 0, 1],
                   [0, 0, 0, 0]])
    v = fv2(gt)
    assert not v.is_mendelian()
    assert v.is_denovo()
    assert not v.is_omission()


def test_denovo_quad_3(fv2):
    gt = np.array([[1, 1, 1, 1],
                   [1, 1, 1, 0]])
    v = fv2(gt)
    assert not v.is_mendelian()
    assert v.is_denovo()
    assert not v.is_omission()


def test_not_denovo_quad_1(fv2):
    gt = np.array([[1, 0, 0, 1],
                   [0, 0, 0, 0]])
    v = fv2(gt)
    assert v.is_mendelian()
    assert not v.is_denovo()
    assert not v.is_omission()
