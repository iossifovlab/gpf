# pylint: disable=W0621,C0114,C0116,W0212,W0613

from collections.abc import Callable

import pytest

from dae.pheno.pheno_data import PhenotypeData, PhenotypeStudy


@pytest.fixture()
def fake_phenotype_data(
    fixture_dirname: Callable[[str], str],
) -> PhenotypeData:
    return PhenotypeStudy(
        "fake_db", fixture_dirname("fake_pheno_db/fake.db"))
