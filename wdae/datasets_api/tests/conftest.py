from __future__ import unicode_literals

import os
import pytest
from box import Box

from pheno.pheno_factory import PhenoFactory
from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb
from datasets_api.views import DatasetView
from datasets_api.models import Dataset


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def dataset_view(variants_db_fixture):
    return DatasetView(variants_db_fixture)


@pytest.fixture(scope='session')
def pheno_factory():
    return PhenoFactory()


@pytest.fixture(scope='session')
def user():
    return Box({'user': {'has_perm': lambda view, dataset: True}})


@pytest.fixture
def recreate_dataset_perm():
    Dataset.recreate_dataset_perm('composite_dataset', [])
    Dataset.recreate_dataset_perm('inheritance_trio', [])
    Dataset.recreate_dataset_perm('quads_composite', [])
    Dataset.recreate_dataset_perm('quads_f1', [])
    Dataset.recreate_dataset_perm('quads_in_child', [])
    Dataset.recreate_dataset_perm('quads_in_parent', [])
    Dataset.recreate_dataset_perm('quads_two_families', [])
    Dataset.recreate_dataset_perm('quads_variant_types', [])


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb
