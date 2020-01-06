import pytest
import numpy as np
from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import Family
from io import StringIO
from dae.utils.variant_utils import GENOTYPE_TYPE, BEST_STATE_TYPE

PED1 = '''
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
'''

PED2 = '''
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f2,          d2,          0,        0,        1,     1,         dad
f2,          m2,          0,        0,        2,     1,         mom
f2,          p2,          d2,       m2,       1,     2,         prb
'''


@pytest.fixture(scope='module')
def fam1():
    ped_df = PedigreeReader.flexible_pedigree_read(
        StringIO(PED1), sep=',')

    family = Family.from_df('f1', ped_df)
    assert len(family.trios) == 1
    return family


@pytest.fixture(scope='module')
def fam2():
    ped_df = PedigreeReader.flexible_pedigree_read(
        StringIO(PED2), sep=',')

    family = Family.from_df('f2', ped_df)
    assert len(family.trios) == 1
    return family


@pytest.fixture(scope='module')
def gt():
    return np.array([[0, 0, 0], [0, 0, 0]], dtype=GENOTYPE_TYPE)


@pytest.fixture(scope='module')
def best_state():
    return np.array([
        [2, 1, 0, 0],
        [0, 1, 2, 1],
        [0, 0, 0, 1]
    ], dtype=BEST_STATE_TYPE)


@pytest.fixture(scope='module')
def best_state_serialized():
    return '\x02\x00\x00\x01\x01\x00\x00\x02\x00\x00\x01\x01'
