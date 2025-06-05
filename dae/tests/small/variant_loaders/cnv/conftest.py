# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap

import pytest

from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import convert_to_tab_separated


@pytest.fixture()
def families() -> FamiliesData:
    ped_content = io.StringIO(convert_to_tab_separated(textwrap.dedent(
        """
            familyId personId dadId	 momId	sex status role
            f1       f1.m     0      0      2   1      mom
            f1       f1.d     0      0      1   1      dad
            f1       f1.p1    f1.d   f1.m   1   2      prb
            f1       f1.s2    f1.d   f1.m   2   1      sib
            f2       f2.m     0      0      2   1      mom
            f2       f2.d     0      0      1   1      dad
            f2       f2.p1    f2.d   f2.m   2   2      prb
        """)))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families
