import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=relative_to_this_test_folder('fixtures'))


@pytest.fixture(scope='session')
def genotype_storage_factory(gpf_instance):
    return gpf_instance.genotype_storage_factory


@pytest.fixture(scope='session')
def filesystem_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage('genotype_filesystem')


@pytest.fixture(scope='session')
def impala_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage('genotype_impala')


@pytest.fixture(scope='session')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='session')
def quads_f1_vcf_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f1_vcf')


@pytest.fixture(scope='session')
def quads_f1_config(gpf_instance, impala_genotype_storage):
    impala_genotype_storage.impala_load_study(
        'quads_f1_impala',
        [relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/variants')],
        [relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/pedigree')]
    )
    gpf_instance.reload_variants_db()
    return gpf_instance.variants_db.get_study_config('quads_f1_impala')
