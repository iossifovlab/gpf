import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.tools.study_parquet_load import load_study_parquet


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))

@pytest.fixture(scope='function')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='function')
def genotype_storage_factory(gpf_instance):
    return gpf_instance.genotype_storage_factory


@pytest.fixture(scope='function')
def filesystem_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage('genotype_filesystem')


@pytest.fixture(scope='function')
def impala_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage('genotype_impala')


@pytest.fixture(scope='function')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='function')
def quads_f1_vcf_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f1_vcf')


@pytest.fixture(scope='function')
def quads_f1_impala_config(gpf_instance, variants_db_fixture, reimport):
    if reimport:
        load_study_parquet(gpf_instance)

    return variants_db_fixture.get_study_config('quads_f1_impala')
