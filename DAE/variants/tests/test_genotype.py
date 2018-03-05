'''
Created on Feb 15, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
import numpy as np
import pytest


def test_11540_gt(ustudy):
    vs = ustudy.query_variants(regions=[Region("1", 11539, 11542)])
    v = next(vs)

    # assert v.position == 11540

    print(v, v.is_mendelian())
    assert v.position == 11540

    print(v.gt)
    assert np.all(np.array(
        [[0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 1, 0, 0, 0, 1, 0, 0, 0]]) == v.gt)

    print(v.best_st)
    assert np.all(np.array(
        [[2, 1, 2, 2, 2, 1, 2, 2, 2],
         [0, 1, 0, 0, 0, 1, 0, 0, 0]]) == v.best_st)


def test_130000_gt(ustudy):
    vs = ustudy.query_variants(regions=[Region("1", 135000, 139999)])
    for v in vs:
        print("-------------------------------------------------------------")
        print(v, v.is_mendelian())
        print(v.gt)
        print(v.best_st)
        print("-------------------------------------------------------------")


def test_11540_130000_gt(ustudy):
    vs = ustudy.query_variants(regions=[Region("1", 11540, 139999)])
    for v in vs:
        print("-------------------------------------------------------------")
        print(v, v.is_mendelian())
        print(v.gt)
        print(v.best_st)
        print("-------------------------------------------------------------")


def test_non_mendelian(ustudy):
    count = 0
    vs = ustudy.query_variants()
    for v in vs:
        if not v.is_mendelian():
            count += 1
    assert count == 140


def test_empty_query(ustudy):

    vs = ustudy.query_variants(regions=[Region("1", 13500, 13999)])
    with pytest.raises(StopIteration):
        _v = next(vs)
