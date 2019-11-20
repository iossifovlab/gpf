import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.studies.study_wrapper import StudyWrapper


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies'))


def datasets_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/datasets'))


@pytest.fixture(scope='session')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def mocked_gene_models(gpf_instance):
    return gpf_instance.genomes_db.get_gene_models()


@pytest.fixture(scope='session')
def dae_config_fixture(gpf_instance):
    return gpf_instance.dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(gpf_instance):
    return gpf_instance.variants_db


@pytest.fixture(scope='session')
def pheno_factory(gpf_instance):
    return gpf_instance.pheno_factory


@pytest.fixture(scope='session')
def weights_factory(gpf_instance):
    return gpf_instance.weights_factory


@pytest.fixture(scope='session')
def genotype_storage_factory(gpf_instance):
    return gpf_instance.genotype_storage_factory


@pytest.fixture(scope='session')
def study_configs(variants_db_fixture):
    return variants_db_fixture.study_configs


@pytest.fixture(scope='session')
def quads_f1_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f1')


@pytest.fixture(scope='session')
def quads_f2_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f2')


def load_study(variants_db_fixture, study_configs, study_name):
    config = study_configs.get(study_name)

    result = variants_db_fixture.make_study(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def inheritance_trio(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'inheritance_trio')


@pytest.fixture(scope='session')
def quads_f1(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_f1')


@pytest.fixture(scope='session')
def quads_f2(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_f2')


@pytest.fixture(scope='session')
def quads_variant_types(variants_db_fixture, study_configs):
    return load_study(
        variants_db_fixture, study_configs, 'quads_variant_types')


@pytest.fixture(scope='session')
def quads_two_families(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_two_families')


@pytest.fixture(scope='session')
def quads_in_child(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_in_child')


@pytest.fixture(scope='session')
def quads_in_parent(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_in_parent')


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(inheritance_trio, pheno_factory, weights_factory):
    return StudyWrapper(inheritance_trio, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_f1_wrapper(quads_f1, pheno_factory, weights_factory):
    return StudyWrapper(quads_f1, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_f2_wrapper(quads_f2, pheno_factory, weights_factory):
    return StudyWrapper(quads_f2, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_variant_types_wrapper(
        quads_variant_types, pheno_factory, weights_factory):
    return StudyWrapper(quads_variant_types, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_two_families_wrapper(
        quads_two_families, pheno_factory, weights_factory):
    return StudyWrapper(quads_two_families, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_in_child_wrapper(quads_in_child, pheno_factory, weights_factory):
    return StudyWrapper(quads_in_child, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_in_parent_wrapper(quads_in_parent, pheno_factory, weights_factory):
    return StudyWrapper(quads_in_parent, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def dataset_configs(variants_db_fixture):
    return variants_db_fixture.dataset_configs


@pytest.fixture(scope='session')
def quads_composite_dataset_config(variants_db_fixture):
    return variants_db_fixture.get_dataset_config('quads_composite_ds')


@pytest.fixture(scope='session')
def composite_dataset_config(variants_db_fixture):
    return variants_db_fixture.get_dataset_config('composite_dataset_ds')


def load_dataset(variants_db_fixture, dataset_configs, dataset_name):
    config = dataset_configs.get(dataset_name)
    assert config is not None, dataset_name

    result = variants_db_fixture.make_dataset(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def inheritance_trio_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'inheritance_trio_ds')


@pytest.fixture(scope='session')
def inheritance_trio_dataset_wrapper(
        inheritance_trio_dataset, pheno_factory, weights_factory):
    return StudyWrapper(
        inheritance_trio_dataset, pheno_factory, weights_factory
    )


@pytest.fixture(scope='session')
def quads_two_families_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_two_families_ds')


@pytest.fixture(scope='session')
def quads_two_families_dataset_wrapper(
        quads_two_families_dataset, pheno_factory, weights_factory):
    return StudyWrapper(
        quads_two_families_dataset, pheno_factory, weights_factory
    )


@pytest.fixture(scope='session')
def quads_f1_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(variants_db_fixture, dataset_configs, 'quads_f1_ds')


@pytest.fixture(scope='session')
def quads_f1_dataset_wrapper(quads_f1_dataset, pheno_factory, weights_factory):
    return StudyWrapper(quads_f1_dataset, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_f2_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(variants_db_fixture, dataset_configs, 'quads_f2_ds')


@pytest.fixture(scope='session')
def quads_f2_dataset_wrapper(quads_f2_dataset, pheno_factory, weights_factory):
    return StudyWrapper(quads_f2_dataset, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_variant_types_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_variant_types_ds')


@pytest.fixture(scope='session')
def quads_variant_types_dataset_wrapper(
        quads_variant_types_dataset, pheno_factory, weights_factory):
    return StudyWrapper(
        quads_variant_types_dataset, pheno_factory, weights_factory
    )


@pytest.fixture(scope='session')
def quads_in_child_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_in_child_ds')


@pytest.fixture(scope='session')
def quads_in_child_dataset_wrapper(
        quads_in_child_dataset, pheno_factory, weights_factory):
    return StudyWrapper(quads_in_child_dataset, pheno_factory, weights_factory)


@pytest.fixture(scope='session')
def quads_in_parent_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_in_parent_ds')


@pytest.fixture(scope='session')
def quads_in_parent_dataset_wrapper(
        quads_in_parent_dataset, pheno_factory, weights_factory):
    return StudyWrapper(
        quads_in_parent_dataset, pheno_factory, weights_factory
    )


@pytest.fixture(scope='session')
def composite_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'composite_dataset_ds')


@pytest.fixture(scope='session')
def composite_dataset_wrapper(
        composite_dataset, pheno_factory, weights_factory):
    return StudyWrapper(composite_dataset, pheno_factory, weights_factory)
