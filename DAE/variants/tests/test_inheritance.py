'''
Created on Feb 14, 2018

@author: lubo
'''
from __future__ import print_function
from RegionOperations import Region
from variants.loader import RawVariantsLoader
import StringIO
from variants.family import Family
from variants.variant import FamilyVariant
import numpy as np
import pytest


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
familyId\tpersonId\tdadId\tmomId\tgender\tstatus\trole
f1\td1\t0\t0\t1\t1\tdad
f1\tm1\t0\t0\t2\t1\tmom
f1\tp1\td1\tm1\t1\t2\tprb
"""


@pytest.fixture(scope='session')
def fam1():
    ped_df = RawVariantsLoader.load_pedigree_file(StringIO.StringIO(PED1))
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
