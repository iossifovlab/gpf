# pylint: disable=W0621,C0114,C0116,W0212,W0613

from typing import Callable

import pytest

from dae.pheno.pheno_data import PhenotypeStudy, PhenotypeData


@pytest.fixture
def fake_phenotype_data(
    fixture_dirname: Callable[[str], str]
) -> PhenotypeData:
    pheno_data = PhenotypeStudy(
        "fake_db", fixture_dirname("fake_pheno_db/fake.db"))
    # pheno_data._load()
    return pheno_data
