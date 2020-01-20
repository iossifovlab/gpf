from io import StringIO

import pytest

from dae.pedigrees.loader import FamiliesLoader
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant


PED1 = '''
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
'''


@pytest.fixture(scope='session')
def fam1():
    families_loader = FamiliesLoader(StringIO(PED1), ped_sep=',')
    families = families_loader.load()
    family = families['f1']
    assert len(family.trios) == 1
    return family


@pytest.fixture(scope='session')
def sv():
    return SummaryVariant([
        SummaryAllele('1', 11539, 'T', None, 0, 0),
        SummaryAllele('1', 11539, 'T', 'TA', 0, 1),
        SummaryAllele('1', 11539, 'T', 'TG', 0, 2)
    ])


@pytest.fixture(scope='session')
def fv1(fam1, sv):
    def rfun(gt, best_st):
        return FamilyVariant(sv, fam1, gt, best_st)
    return rfun
