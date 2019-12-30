import os
from io import StringIO
import pytest
from dae.pedigrees.family import Family
from dae.pedigrees.family import FamiliesLoader


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


PED1 = '''
# SIMPLE TRIO
familyId,    personId,    dadId,    momId,    sex,   status,    role
f1,          d1,          0,        0,        1,     1,         dad
f1,          m1,          0,        0,        2,     1,         mom
f1,          p1,          d1,       m1,       1,     2,         prb
'''


@pytest.fixture(scope='function')
def sample_family():
    ped_df = FamiliesLoader.flexible_pedigree_read(
        StringIO(PED1), sep=',')

    family = Family.from_df('f1', ped_df)
    assert len(family.trios) == 1
    return family
