# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from pytest_mock.plugin import MockerFixture

from dae.gpf_instance.gpf_instance import GPFInstance
from impala_storage.schema1.impala_dataset_helpers import ImpalaDatasetHelpers


def test_find_genotype_data_config_file(
    fixtures_gpf_instance: GPFInstance,
) -> None:
    helpers = ImpalaDatasetHelpers(fixtures_gpf_instance)
    fname = helpers.find_genotype_data_config_file("Study1")
    assert fname is not None


def test_find_genotype_data_config(fixtures_gpf_instance: GPFInstance) -> None:
    print(fixtures_gpf_instance.get_genotype_data_ids())
    helpers = ImpalaDatasetHelpers(fixtures_gpf_instance)
    res = helpers.find_genotype_data_config("Study1")

    assert res is not None
    assert res.id == "Study1"


def test_is_impala_genotype_data_config(
    fixtures_gpf_instance: GPFInstance,
) -> None:
    print(fixtures_gpf_instance.get_genotype_data_ids())
    helpers = ImpalaDatasetHelpers(fixtures_gpf_instance)
    assert not helpers.is_impala_genotype_storage("Study1")


def test_rename_study_config(
    fixtures_gpf_instance: GPFInstance, mocker: MockerFixture,
) -> None:
    def mock_rename(name1: str, name2: str) -> None:
        print(name1)
        print(name2)

    mocker.patch("os.rename", mock_rename)

    mock_open = mocker.mock_open()
    mocker.patch("dae.studies.dataset_helpers.open", mock_open)

    spy = mocker.spy(os, "rename")

    helpers = ImpalaDatasetHelpers(fixtures_gpf_instance)

    helpers.rename_study_config("Study1", "new", {})

    print(spy.mock_calls)
    print(mock_open.mock_calls)

    assert len(spy.mock_calls) == 2
    assert len(mock_open.mock_calls) == 4


def test_remove_study_config(
    fixtures_gpf_instance: GPFInstance,
    mocker: MockerFixture,
) -> None:
    def mock_remove(fname: str) -> None:
        assert fname.endswith("Study1")

    mocker.patch("shutil.rmtree", mock_remove)

    helpers = ImpalaDatasetHelpers(fixtures_gpf_instance)
    helpers.remove_study_config("Study1")
