import os
from io import StringIO
import pytest

from dae.pedigrees.loader import FamiliesLoader


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
    families_loader = FamiliesLoader(StringIO(PED1), ped_sep=',')
    families = families_loader.load()
    family = families['f1']
    assert len(family.trios) == 1
    return family
