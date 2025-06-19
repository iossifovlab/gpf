# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.variants_db import VariantsDb


@pytest.fixture(scope="session")
def variants_db_fixture(t4c8_instance: GPFInstance) -> VariantsDb:
    return t4c8_instance._variants_db


def test_get_genotype_study_config_valid(
    variants_db_fixture: VariantsDb,
) -> None:
    assert variants_db_fixture\
        .get_genotype_study_config("t4c8_study_1") is not None


def test_get_genotype_study_config_invalid(
    variants_db_fixture: VariantsDb,
) -> None:
    assert variants_db_fixture.get_genotype_study_config("ala bala") is None


def test_get_genotype_study_valid(variants_db_fixture: VariantsDb) -> None:
    study = variants_db_fixture.get_genotype_study("t4c8_study_1")
    assert study is not None


def test_get_genotype_study_invalid(variants_db_fixture: VariantsDb) -> None:
    study = variants_db_fixture.get_genotype_study("ala bala")
    assert study is None


def test_get_all_genotype_group_ids(variants_db_fixture: VariantsDb) -> None:
    assert set(variants_db_fixture.get_all_genotype_group_ids()) == {
        "t4c8_dataset",
    }


def test_get_genotype_group_config_valid(
    variants_db_fixture: VariantsDb,
) -> None:
    assert variants_db_fixture.\
        get_genotype_group_config("t4c8_dataset") is not None


def test_get_genotype_group_config_invalid(
    variants_db_fixture: VariantsDb,
) -> None:
    assert variants_db_fixture.\
        get_genotype_group_config("ala bala") is None


def test_get_genotype_group_valid(variants_db_fixture: VariantsDb) -> None:
    genotype_data_group = variants_db_fixture.get_genotype_group(
        "t4c8_dataset",
    )
    assert genotype_data_group is not None
    assert genotype_data_group.study_id == "t4c8_dataset"


def test_get_genotype_group_invalid(
    variants_db_fixture: VariantsDb,
) -> None:
    genotype_data_group = variants_db_fixture.get_genotype_group(
        "ala bala",
    )
    assert genotype_data_group is None


def test_get_all_genotype_groups(variants_db_fixture: VariantsDb) -> None:
    genotype_data_groups = variants_db_fixture.get_all_genotype_groups()
    assert len(genotype_data_groups) == 1


def test_get_valid(variants_db_fixture: VariantsDb) -> None:
    assert variants_db_fixture.get("t4c8_study_1") is not None
    assert variants_db_fixture.get("t4c8_dataset") is not None


def test_get_invalid(variants_db_fixture: VariantsDb) -> None:
    assert variants_db_fixture.get("ala bala") is None


def test_get_all(variants_db_fixture: VariantsDb) -> None:
    studies = variants_db_fixture.get_all_genotype_data()
    assert len(studies) == 5


def test_make_genotype_study(
    variants_db_fixture: VariantsDb,
) -> None:
    test_config = variants_db_fixture.get_genotype_study_config("t4c8_study_1")
    assert test_config is not None
    assert (
        variants_db_fixture._make_genotype_study(test_config) is not None
    )
