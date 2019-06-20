from __future__ import unicode_literals

import os
import pytest

from gene.config import DenovoGeneSetCollectionConfig
from gene.denovo_gene_sets_collection import DenovoGeneSetsCollection

from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb
from datasets_api.studies_manager import StudiesManager


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='function')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture(scope='function')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='function')
def studies_manager(dae_config_fixture):
    return StudiesManager(dae_config_fixture)


@pytest.fixture(scope='function')
def mock_studies_manager(db, mocker, studies_manager):
    studies_manager.reload_dataset()
    mocker.patch(
        'gene_sets.views.get_studies_manager',
        return_value=studies_manager)
    mocker.patch(
        'datasets_api.permissions.get_studies_manager',
        return_value=studies_manager)


@pytest.fixture(scope='function')
def calc_gene_sets(request, denovo_gene_sets):
    for dgs in denovo_gene_sets:
        dgs.load(build_cache=True)

    print("PRECALCULATION COMPLETE")

    def remove_gene_sets():
        for dgs in denovo_gene_sets:
            os.remove(dgs.config.denovo_gene_set_cache_file('phenotype'))
    request.addfinalizer(remove_gene_sets)


def get_denovo_gene_sets_by_id(variants_db_fixture, dgs_id):
    denovo_gene_set_config = DenovoGeneSetCollectionConfig.from_config(
        variants_db_fixture.get_config(dgs_id))

    return DenovoGeneSetsCollection(
        variants_db_fixture.get(dgs_id), denovo_gene_set_config)


@pytest.fixture(scope='function')
def denovo_gene_sets(variants_db_fixture):
    return [
        get_denovo_gene_sets_by_id(variants_db_fixture, 'f1_group'),
        get_denovo_gene_sets_by_id(variants_db_fixture, 'f2_group'),
        get_denovo_gene_sets_by_id(variants_db_fixture, 'f3_group')
    ]
