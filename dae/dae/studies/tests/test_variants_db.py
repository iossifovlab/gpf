import os

from dae.studies.tests.conftest import fixtures_dir
from dae.studies.variants_db import VariantsDb


def test_fixture_variants_db_can_be_loaded(variants_db_fixture):
    assert variants_db_fixture is not None


def test_variants_db_can_create_study_from_config(
        study_configs, variants_db_fixture):
    test_config = study_configs.get('quads_f1')

    assert variants_db_fixture.make_study(test_config) is not None


##############################################################


def test_variants_db_studies_simple(
        dae_config_fixture, pheno_factory, weights_factory):
    assert dae_config_fixture is not None
    assert dae_config_fixture.studies_db.dir is not None

    assert dae_config_fixture.studies_db.dir == \
        os.path.join(fixtures_dir(), "studies")

    vdb = VariantsDb(dae_config_fixture, pheno_factory, weights_factory)
    assert vdb is not None


def test_variants_db_datasets_simple(
        dae_config_fixture, pheno_factory, weights_factory):
    assert dae_config_fixture is not None
    assert dae_config_fixture.datasets_db.dir is not None

    assert dae_config_fixture.datasets_db.dir == \
        os.path.join(fixtures_dir(), "datasets")

    vdb = VariantsDb(dae_config_fixture, pheno_factory, weights_factory)
    assert vdb is not None


def test_get_existing_study_config(variants_db_fixture):
    assert variants_db_fixture.get_study_config('quads_f1') is not None


def test_get_non_existing_study_config(variants_db_fixture):
    assert variants_db_fixture.get_study_config('ala bala') is None


def test_get_existing_study(variants_db_fixture):
    study = variants_db_fixture.get_study('inheritance_trio')
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_study(variants_db_fixture):
    study = variants_db_fixture.get_study('ala bala')
    assert study is None


def test_get_existing_study_wrapper(variants_db_fixture):
    study = variants_db_fixture.get_study_wdae_wrapper('inheritance_trio')
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_study_wrapper(variants_db_fixture):
    study = variants_db_fixture.get_study_wdae_wrapper('ala bala')
    assert study is None


def test_get_all_studies(variants_db_fixture):
    studies = variants_db_fixture.get_all_studies()
    assert len(studies) == 7


##############################################################


def test_get_datasets_ids(variants_db_fixture):
    assert sorted(variants_db_fixture.get_datasets_ids()) == \
        sorted([
            'quads_in_parent_ds', 'composite_dataset_ds', 'quads_in_child_ds',
            'quads_composite_ds', 'inheritance_trio_ds',
            'quads_two_families_ds', 'quads_variant_types_ds', 'quads_f1_ds',
            'quads_f2_ds'
        ])


def test_get_existing_dataset_config(variants_db_fixture):
    vdb = variants_db_fixture
    assert vdb.get_dataset_config('inheritance_trio_ds') is not None


def test_get_non_existing_dataset_config(variants_db_fixture):
    assert variants_db_fixture.get_dataset_config('ala bala') is None


def test_get_dataset(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset('quads_in_parent_ds')
    assert dataset is not None
    assert dataset.id == 'quads_in_parent_ds'


def test_get_existing_dataset(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset('inheritance_trio_ds')
    assert dataset is not None
    vs = dataset.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_dataset(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset('ala bala')
    assert dataset is None


def test_get_existing_dataset_wrapper(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset_wdae_wrapper(
        'inheritance_trio_ds')
    assert dataset is not None
    vs = dataset.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_dataset_wrapper(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset_wdae_wrapper('ala bala')
    assert dataset is None


def test_get_all_datasets(variants_db_fixture):
    datasets = variants_db_fixture.get_all_datasets()
    assert len(datasets) == 9


def test_get_all_dataset_configs(variants_db_fixture):
    configs = variants_db_fixture.get_all_dataset_configs()
    assert len(configs) == 9


##############################################################


def test_get_existing_config(variants_db_fixture):
    vdb = variants_db_fixture
    assert vdb.get_config('inheritance_trio') is not None


def test_get_non_existing_config(variants_db_fixture):
    assert variants_db_fixture.get_config('ala bala') is None


def test_get_existing(variants_db_fixture):
    study = variants_db_fixture.get('inheritance_trio')
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 14

    dataset = variants_db_fixture.get('inheritance_trio_ds')
    assert dataset is not None
    vs = dataset.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing(variants_db_fixture):
    study = variants_db_fixture.get('ala bala')
    assert study is None


def test_get_existing_wrapper(variants_db_fixture):
    study = variants_db_fixture.get_wdae_wrapper(
        'inheritance_trio')
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 14

    dataset = variants_db_fixture.get_wdae_wrapper(
        'inheritance_trio_ds')
    assert dataset is not None
    vs = dataset.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_wrapper(variants_db_fixture):
    study = variants_db_fixture.get_wdae_wrapper('ala bala')
    assert study is None


def test_get_all(variants_db_fixture):
    studies = variants_db_fixture.get_all()
    assert len(studies) == 16
