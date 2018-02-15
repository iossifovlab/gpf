'''
Created on Feb 14, 2018

@author: lubo
'''
from __future__ import print_function

import StringIO

import pytest

from RegionOperations import Region
import numpy as np
from variants.family import Family
from variants.loader import RawVariantsLoader
from variants.variant import FamilyVariant


def test_mendelian(uagre):
    df = uagre.query_regions([Region("1", 11541, 54721)])

    res_df, variants = uagre.query_families(['AU1921'], df)
    assert len(res_df) == 5
    assert len(variants) == 5

    for vs in variants.values():
        for v in vs:
            print(v, v.is_medelian(), v.effect_type)
            print(v.best_st)
            print(v.gt)


PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    gender,    status,    role
f1,          d1,          0,        0,        1,         1,         dad
f1,          m1,          0,        0,        2,         1,         mom
f1,          p1,          d1,       m1,       1,         2,         prb
"""


@pytest.fixture(scope='session')
def fam1():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED1), sep=",")
    print(ped_df.dtypes)
    print(ped_df)
    print(ped_df.to_dict(orient='records'))

    family = Family("f1", ped_df)
    assert len(family.trios) == 1
    return family


@pytest.fixture(scope='session')
def fv1(fam1):
    v = FamilyVariant("1", 11539, "T", "TA")
    v.set_family(fam1)
    return v


def test_mendelian_simple_1(fv1):
    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [0, 0, 0]])
    assert v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[0, 0, 1],
                     [0, 0, 0]])
    assert not v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [0, 0, 1]])
    assert not v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[1, 0, 0],
                     [0, 0, 1]])
    assert v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[0, 0, 0],
                     [1, 0, 1]])
    assert v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[1, 0, 0],
                     [1, 0, 1]])
    assert v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[1, 1, 0],
                     [1, 0, 1]])
    assert v.is_medelian()

    v = fv1.clone()
    v.gt = np.array([[1, 1, 1],
                     [1, 0, 1]])
    assert v.is_medelian()


PED2 = """
# SIMPLE QUAD
familyId,    personId,    dadId,    momId,    gender,    status,    role
f1,          d1,          0,        0,        1,         1,         dad
f1,          m1,          0,        0,        2,         1,         mom
f1,          p1,          d1,       m1,       1,         2,         prb
f1,          s1,          d1,       m1,       1,         1,         sib
"""


@pytest.fixture(scope='session')
def fam2():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED2), sep=',')
    print(ped_df.dtypes)
    print(ped_df)
    print(ped_df.to_dict(orient='records'))

    family = Family("f1", ped_df)
    assert len(family.trios) == 2
    return family


@pytest.fixture(scope='session')
def fv2(fam2):
    v = FamilyVariant("1", 11539, "T", "TA")
    v.set_family(fam2)
    return v


def test_mendelian_simple_2(fv2):
    v = fv2.clone()
    v.gt = np.array([[0, 0, 0, 0],
                     [0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[1, 1, 0, 0],
                     [0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 0],
                     [0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [0, 0, 1, 1]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [1, 1, 1, 1]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[1, 1, 1, 1],
                     [0, 0, 1, 1]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 1],
                     [0, 1, 1, 1]])
    assert not v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 1],
                     [0, 1, 0, 1]])
    assert not v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 1],
                     [0, 1, 0, 0]])
    assert v.is_medelian()

    v = fv2.clone()
    v.gt = np.array([[0, 1, 1, 0],
                     [0, 1, 0, 1]])
    assert v.is_medelian()


PED3 = """
# TWO GENERATION PEDIGREE
familyId, personId, dadId, momId, gender, status, role
f1,       gd1,      0,     0,     1,      1,      pathernal_grandfather
f1,       gm1,      0,     0,     2,      1,      pathernal_grandmother
f1,       d1,       gd1,   gm1,   1,      1,      dad
f1,       m1,       0,     0,     2,      1,      mom
f1,       p1,       d1,    m1,    1,      2,      prb
"""


@pytest.fixture(scope='session')
def fam3():
    ped_df = RawVariantsLoader.load_pedigree_file(
        StringIO.StringIO(PED3), sep=',')

    family = Family("f1", ped_df)
    assert len(family.trios) == 2
    return family


@pytest.fixture(scope='session')
def fv3(fam3):
    v = FamilyVariant("1", 11539, "T", "TA")
    v.set_family(fam3)
    return v


def test_mendelian_simple_3(fv3):
    v = fv3.clone()
    v.gt = np.array([[0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv3.clone()
    v.gt = np.array([[1, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv3.clone()
    v.gt = np.array([[1, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0]])
    assert not v.is_medelian()

    v = fv3.clone()
    v.gt = np.array([[1, 0, 1, 0, 0],
                     [1, 0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv3.clone()
    v.gt = np.array([[1, 1, 1, 0, 0],
                     [1, 0, 0, 0, 0]])
    assert v.is_medelian()

    v = fv3.clone()
    v.gt = np.array([[1, 1, 1, 0, 0],
                     [1, 0, 1, 0, 0]])
    assert not v.is_medelian()

    v = fv3.clone()
    v.gt = np.array([[1, 1, 1, 0, 1],
                     [1, 0, 1, 0, 0]])
    assert v.is_medelian()
