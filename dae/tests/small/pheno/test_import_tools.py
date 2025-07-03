# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from argparse import Namespace
from pathlib import Path

import pytest
import pytest_mock
from dae.genomic_resources.testing import setup_directories
from dae.pheno.common import PhenoImportConfig
from dae.pheno.import_tools import main


@pytest.fixture
def test_dir(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    root_path = tmp_path_factory.mktemp("import_tools_test_fixtures")
    setup_directories(root_path, {
        "conf_1.yaml": textwrap.dedent("""
            id: first
            work_dir: test_out
            instrument_files:
                - instruments/i1.csv
            pedigree: family.ped
            person_column: person_id
        """),
        "conf_2.yaml": textwrap.dedent("""
            id: first
            input_dir: test_inp
            work_dir: test_out
            instrument_files:
                - instruments/i1.csv
            pedigree: family.ped
            person_column: person_id
        """),
        "conf_3.yaml": textwrap.dedent("""
            id: first
            input_dir: /home/user/test_inp
            work_dir: test_out
            instrument_files:
                - instruments/i1.csv
            pedigree: family.ped
            person_column: person_id
        """),
        "conf_4.yaml": textwrap.dedent("""
            id: first
            work_dir: /home/user/test_out
            instrument_files:
                - instruments/i1.csv
            pedigree: family.ped
            person_column: person_id
        """),
    })
    return root_path


def test_pheno_import_tool(
    mocker: pytest_mock.MockerFixture,
    test_dir: Path,
) -> None:
    mocked_import_func = \
        mocker.patch("dae.pheno.import_tools.import_pheno_data")
    main([str(test_dir / "conf_1.yaml")])
    assert mocked_import_func.call_count == 1
    assert mocked_import_func.call_args[0][0] == \
        PhenoImportConfig(
            id="first",
            input_dir=str(test_dir),
            work_dir=str(test_dir / "test_out"),
            instrument_files=["instruments/i1.csv"],
            pedigree="family.ped",
            person_column="person_id",
            delimiter=",",
            skip_pedigree_measures=False,
            inference_config=None,
            data_dictionary=None,
            study_config=None,
        )
    assert mocked_import_func.call_args[0][2] == Namespace(
        verbose=None,
        jobs=None,
        dask_cluster_name=None,
        dask_cluster_config_file=None,
        task_log_dir=f"{test_dir}/test_out/.task-log/first",
        task_ids=None,
        keep_going=False,
        force=False,
        task_status_dir=f"{test_dir}/test_out/.task-progress/first",
    )


def test_pheno_import_tool_input_dir_default(
    mocker: pytest_mock.MockerFixture,
    test_dir: Path,
) -> None:
    # The scenario is the same as in the general test "test_pheno_import_tool",
    # but for the sake of granularity, this test checks only the default input
    # dir has been correctly set.
    mocked_import_func = \
        mocker.patch("dae.pheno.import_tools.import_pheno_data")
    main([str(test_dir / "conf_1.yaml")])
    assert mocked_import_func.call_args[0][0].input_dir == str(test_dir)


def test_pheno_import_tool_input_dir_relative(
    mocker: pytest_mock.MockerFixture,
    test_dir: Path,
) -> None:
    mocked_import_func = \
        mocker.patch("dae.pheno.import_tools.import_pheno_data")
    main([str(test_dir / "conf_2.yaml")])
    assert mocked_import_func.call_args[0][0].input_dir == \
        str(test_dir / "test_inp")


def test_pheno_import_tool_input_dir_absolute(
    mocker: pytest_mock.MockerFixture,
    test_dir: Path,
) -> None:
    mocked_import_func = \
        mocker.patch("dae.pheno.import_tools.import_pheno_data")
    main([str(test_dir / "conf_3.yaml")])
    assert mocked_import_func.call_args[0][0].input_dir == \
        "/home/user/test_inp"


def test_pheno_import_tool_work_dir_relative(
    mocker: pytest_mock.MockerFixture,
    test_dir: Path,
) -> None:
    # The scenario is the same as in the general test "test_pheno_import_tool",
    # but for the sake of granularity, this test checks only the relative
    # output dir has been correctly resolved.
    mocked_import_func = \
        mocker.patch("dae.pheno.import_tools.import_pheno_data")
    main([str(test_dir / "conf_1.yaml")])
    assert mocked_import_func.call_args[0][0].work_dir == \
        str(test_dir / "test_out")


def test_pheno_import_tool_work_dir_absolute(
    mocker: pytest_mock.MockerFixture,
    test_dir: Path,
) -> None:
    mocked_import_func = \
        mocker.patch("dae.pheno.import_tools.import_pheno_data")
    main([str(test_dir / "conf_4.yaml")])
    assert mocked_import_func.call_args[0][0].work_dir == \
        "/home/user/test_out"
