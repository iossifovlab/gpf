# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

import pytest
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData


@pytest.fixture(scope="session")
def fake_families(fixture_dirname):
    ped_df = FamiliesLoader.flexible_pedigree_read(
        fixture_dirname("denovo_import/fake_pheno.ped")
    )
    result = FamiliesData.from_pedigree_df(ped_df)
    return result
