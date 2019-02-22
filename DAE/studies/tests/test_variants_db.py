import os
from .conftest import fixtures_dir
from ..factory import VariantsDb


def test_variants_db_studies_simple(dae_config_fixture):
    assert dae_config_fixture is not None
    assert dae_config_fixture.studies_dir is not None

    assert dae_config_fixture.studies_dir == \
        os.path.join(fixtures_dir(), "studies")

    vdb = VariantsDb(dae_config_fixture)
    assert vdb is not None


def test_variants_db_datasets_simple(dae_config_fixture):
    assert dae_config_fixture is not None
    assert dae_config_fixture.datasets_dir is not None

    assert dae_config_fixture.datasets_dir == \
        os.path.join(fixtures_dir(), "datasets")

    vdb = VariantsDb(dae_config_fixture)
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


##############################################################


def test_get_existing_dataset_config(variants_db_fixture):
    vdb = variants_db_fixture
    assert vdb.get_dataset_config('inheritance_trio') is not None


def test_get_non_existing_dataset_config(variants_db_fixture):
    assert variants_db_fixture.get_dataset_config('ala bala') is None


def test_get_existing_dataset(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset('inheritance_trio')
    assert dataset is not None
    vs = dataset.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_dataset(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset('ala bala')
    assert dataset is None


def test_get_existing_dataset_wrapper(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset_wdae_wrapper('inheritance_trio')
    assert dataset is not None
    vs = dataset.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_dataset_wrapper(variants_db_fixture):
    dataset = variants_db_fixture.get_dataset_wdae_wrapper('ala bala')
    assert dataset is None
