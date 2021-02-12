import pytest

from dae.pheno.pheno_db import PhenotypeDataStudy
from dae.utils.person_filters import PhenoFilterBuilder


@pytest.fixture
def fake_phenotype_data(fixture_dirname):
    pheno_data = PhenotypeDataStudy(fixture_dirname("fake_pheno_db/fake.db"))
    pheno_data._load()
    return pheno_data


@pytest.fixture
def filter_builder(fake_phenotype_data):
    builder = PhenoFilterBuilder(fake_phenotype_data)
    return builder
