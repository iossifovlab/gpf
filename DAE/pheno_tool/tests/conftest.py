import pytest

from pheno.pheno_db import PhenoDB
from pheno_tool.pheno_common import PhenoFilterBuilder


@pytest.fixture
def fake_pheno_db(fixture_dirname):
    pheno_db = PhenoDB(fixture_dirname('fake_pheno_db/fake.db'))
    pheno_db.load()
    return pheno_db


@pytest.fixture
def filter_builder(fake_pheno_db):
    builder = PhenoFilterBuilder(fake_pheno_db)
    return builder
