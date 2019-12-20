import pytest

import os


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )

@pytest.fixture(scope='session')
def work_dir():
    return relative_to_this_test_folder('fixtures')


@pytest.fixture(scope='session')
def local_gpf_instance(gpf_instance, work_dir):
    return gpf_instance(work_dir=work_dir)


@pytest.fixture(scope='session')
def genotype_storage_factory(local_gpf_instance):
    return local_gpf_instance._genotype_storage_factory


@pytest.fixture(scope='session')
def filesystem_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage('genotype_filesystem')


@pytest.fixture(scope='session')
def impala_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage('genotype_impala')


@pytest.fixture(scope='session')
def variants_db_fixture(local_gpf_instance):
    return local_gpf_instance._variants_db


@pytest.fixture(scope='session')
def quads_f1_vcf_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f1_vcf')


@pytest.fixture(scope='session')
def quads_f1_config(local_gpf_instance, impala_genotype_storage):
    impala_genotype_storage.impala_load_study(
        'quads_f1_impala',
        variant_paths=[relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/variants')],
        pedigree_paths=[relative_to_this_test_folder(
            'fixtures/studies/quads_f1_impala/data/pedigree')]
    )
    local_gpf_instance.reload()
    return local_gpf_instance._variants_db.get_study_config('quads_f1_impala')
