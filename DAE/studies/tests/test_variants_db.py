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


def test_get_existing_study_config(variants_db_fixture):
    assert variants_db_fixture.get_study_config('quads_f1') is not None


def test_get_non_existing_study_config(variants_db_fixture):
    assert variants_db_fixture.get_study_config('ala bala') is None


def test_get_existing_study(variants_db_fixture):
    study = variants_db_fixture.get_study('quads_f1')
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 2


def test_get_non_existing_study(variants_db_fixture):
    study = variants_db_fixture.get_study('ala bala')
    assert study is None


def test_get_existing_study_wrapper(variants_db_fixture):
    study = variants_db_fixture.get_study_wdae_wrapper('quads_f1')
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 2


def test_get_non_existing_study_wrapper(variants_db_fixture):
    study = variants_db_fixture.get_study_wdae_wrapper('ala bala')
    assert study is None
