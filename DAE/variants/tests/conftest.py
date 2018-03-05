'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function

import StringIO

import pytest

from variants.configure import Configure
from variants.family import Family
from variants.loader import RawVariantsLoader
from variants.raw_vcf import RawFamilyVariants
from variants.variant import FamilyVariant
import os


@pytest.fixture(scope='session')
def ustudy_config():
    config = Configure.from_config()
    return config


@pytest.fixture(scope='session')
def ustudy_loader(ustudy_config):
    return RawVariantsLoader(ustudy_config)


@pytest.fixture(scope='session')
def ustudy(ustudy_config):
    fvariants = RawFamilyVariants(ustudy_config)
    return fvariants


@pytest.fixture(scope='session')
def rvcf_config():
    from variants.default_settings import DATA_DIR
    prefix = os.path.join(DATA_DIR, "ssc_nygc/ussc")
    config = Configure.from_prefix(prefix)
    return config


@pytest.fixture(scope='session')
def rvcf(rvcf_config):
    fvariants = RawFamilyVariants(rvcf_config)
    return fvariants


PED1 = """
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
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


PED2 = """
# SIMPLE QUAD
familyId,    personId,    dadId,    momId,    sex,    status,    role
f1,          d1,          0,        0,        1,      1,         dad
f1,          m1,          0,        0,        2,      1,         mom
f1,          p1,          d1,       m1,       1,      2,         prb
f1,          s1,          d1,       m1,       1,      1,         sib
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


PED3 = """
# TWO GENERATION PEDIGREE
familyId, personId, dadId, momId, sex,   status, role
f1,       gd1,      0,     0,     1,     1,      pathernal_grandfather
f1,       gm1,      0,     0,     2,     1,      pathernal_grandmother
f1,       d1,       gd1,   gm1,   1,     1,      dad
f1,       m1,       0,     0,     2,     1,      mom
f1,       p1,       d1,    m1,    1,     2,      prb
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
