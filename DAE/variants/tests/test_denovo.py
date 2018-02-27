'''
Created on Feb 27, 2018

@author: lubo
'''
from __future__ import print_function

import numpy as np


def test_denovo_trio_1(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 1],
                     [0, 0, 0]])
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_denovo_trio_2(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 1],
                     [0, 0, 1]])
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_denovo_trio_3(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [0, 0, 1]])
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_not_denovo_trio_1(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [0, 0, 0]])
    assert v.is_mendelian()
    assert not v.is_denovo()


def test_not_denovo_trio_2(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 1, 0],
                     [0, 1, 0]])
    assert not v.is_mendelian()
    assert not v.is_denovo()
    assert v.is_omission()


def test_denovo_quad_1(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 0, 1, 0],
                     [0, 0, 0, 0]])
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_denovo_quad_2(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 0, 0, 1],
                     [0, 0, 0, 0]])
    assert not v.is_mendelian()
    assert v.is_denovo()


def test_not_denovo_quad_1(fv2):
    v = fv2.clone()
    v.gt = np.array([[1, 0, 0, 1],
                     [0, 0, 0, 0]])
    assert v.is_mendelian()
    assert not v.is_denovo()
