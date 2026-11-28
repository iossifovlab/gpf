# pylint: disable=W0621,C0114,C0116,W0212,W0613,R0917
import logging
import pathlib
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
import pytest_mock

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.schema2_storage.schema2_import_storage import Schema2ImportStorage
from gpf.tools import reannotate_instance
from gpf.tools.reannotate_instance import ReannotateInstanceTool


@pytest.fixture
def study_ids(t4c8_instance: GPFInstance) -> list[str]:
    """The ids of the studies that are not groups, in the instance order."""
    result = [
        study.study_id
        for study in t4c8_instance.get_all_genotype_data()
        if not study.is_group
    ]
    assert sorted(result) == [
        "t4c8_study_1", "t4c8_study_2", "t4c8_study_3", "t4c8_study_4"]
    return result


@pytest.fixture
def make_tool(
    t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> Callable[..., ReannotateInstanceTool]:
    """Build the tool on the t4c8 instance, without the global context."""
    mocker.patch.object(reannotate_instance, "context_providers_init")
    context = MagicMock()
    context.get_context_object.return_value = t4c8_instance
    mocker.patch.object(
        reannotate_instance, "get_genomic_context", return_value=context)

    def builder(*extra_args: str) -> ReannotateInstanceTool:
        return ReannotateInstanceTool(
            ["--work-dir", str(tmp_path), *extra_args])

    return builder


@pytest.fixture
def up_to_date(mocker: pytest_mock.MockerFixture) -> MagicMock:
    return mocker.patch.object(
        ReannotateInstanceTool, "_is_study_annotation_up_to_date",
        return_value=False)


@pytest.fixture
def task_graph(mocker: pytest_mock.MockerFixture) -> dict[str, MagicMock]:
    return {
        "generate": mocker.patch.object(
            Schema2ImportStorage, "generate_reannotate_task_graph"),
        "process": mocker.patch.object(
            reannotate_instance.TaskGraphCli, "process_graph"),
    }


def test_run_without_gpf_instance_raises_value_error(
    make_tool: Callable[..., ReannotateInstanceTool],
) -> None:
    tool = make_tool()
    tool.gpf_instance = None  # type: ignore[assignment]

    with pytest.raises(
            ValueError, match="No configured GPF instance to work with!"):
        tool.run()


def test_run_with_up_to_date_studies_logs_nothing_to_be_done(
    make_tool: Callable[..., ReannotateInstanceTool],
    mocker: pytest_mock.MockerFixture,
    task_graph: dict[str, MagicMock],
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mocker.patch.object(
        ReannotateInstanceTool, "_is_study_annotation_up_to_date",
        return_value=True)
    tool = make_tool()

    with caplog.at_level(logging.INFO, logger=reannotate_instance.__name__):
        tool.run()

    assert "Nothing to be done." in caplog.messages
    assert capsys.readouterr().out == ""
    task_graph["generate"].assert_not_called()
    task_graph["process"].assert_not_called()


def test_run_checks_only_the_studies_that_are_not_groups(
    make_tool: Callable[..., ReannotateInstanceTool],
    t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
    up_to_date: MagicMock,
    study_ids: list[str],
) -> None:
    tool = make_tool("--dry-run")

    tool.run()

    checked = [call.args for call in up_to_date.call_args_list]
    assert checked == [
        (study_id, t4c8_instance, tmp_path / "check" / study_id)
        for study_id in study_ids
    ]


@pytest.mark.usefixtures("up_to_date")
def test_dry_run_prints_the_studies_and_runs_no_task_graph(
    make_tool: Callable[..., ReannotateInstanceTool],
    task_graph: dict[str, MagicMock],
    capsys: pytest.CaptureFixture[str],
    study_ids: list[str],
) -> None:
    tool = make_tool("--dry-run")

    tool.run()

    assert capsys.readouterr().out.splitlines() == [
        "Studies to be reannotated:",
        *(f"-> {study_id}" for study_id in study_ids),
    ]
    task_graph["generate"].assert_not_called()
    task_graph["process"].assert_not_called()


def test_run_skips_a_remote_study(
    make_tool: Callable[..., ReannotateInstanceTool],
    t4c8_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
    up_to_date: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    remote = MagicMock(is_group=False, is_remote=True, study_id="remote")
    mocker.patch.object(
        t4c8_instance, "get_all_genotype_data", return_value=[remote])
    tool = make_tool()

    with caplog.at_level(logging.INFO, logger=reannotate_instance.__name__):
        tool.run()

    up_to_date.assert_not_called()
    assert "Nothing to be done." in caplog.messages


@pytest.mark.parametrize(
    "storage_type, expected_out",
    [
        ("parquet", ["Studies to be reannotated:", "-> t4c8_study_1"]),
        ("duckdb_parquet",
         ["Studies to be reannotated:", "-> t4c8_study_1"]),
        ("inmemory", []),
    ],
)
def test_run_keeps_only_the_parquet_storage_types(
    make_tool: Callable[..., ReannotateInstanceTool],
    t4c8_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
    up_to_date: MagicMock,
    capsys: pytest.CaptureFixture[str],
    storage_type: str,
    expected_out: list[str],
) -> None:
    study = t4c8_instance.get_genotype_data("t4c8_study_1")
    mocker.patch.object(
        t4c8_instance, "get_all_genotype_data", return_value=[study])
    storage = MagicMock(storage_type=storage_type)
    registry = t4c8_instance.genotype_storages
    mocker.patch.object(
        registry, "get_default_genotype_storage", return_value=storage)
    mocker.patch.object(
        registry, "get_genotype_storage", return_value=storage)
    tool = make_tool("--dry-run")

    tool.run()

    assert capsys.readouterr().out.splitlines() == expected_out
    # The up-to-date check runs before the check of the storage type.
    up_to_date.assert_called_once()


def test_run_raises_for_a_study_with_another_storage_type(
    make_tool: Callable[..., ReannotateInstanceTool],
    t4c8_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    study = t4c8_instance.get_genotype_data("t4c8_study_1")
    mocker.patch.object(
        t4c8_instance, "get_all_genotype_data", return_value=[study])
    mocker.patch.object(
        t4c8_instance, "get_annotation_pipeline",
        return_value=MagicMock(**{"get_info.return_value": []}))
    mocker.patch.object(
        t4c8_instance.genotype_storages, "get_genotype_storage",
        return_value=MagicMock(storage_type="inmemory"))
    tool = make_tool("--dry-run")

    with pytest.raises(ValueError, match="Invalid storage type inmemory"):
        tool.run()


@pytest.mark.parametrize("full_reannotation", [False, True])
@pytest.mark.usefixtures("up_to_date")
def test_run_reannotates_each_study_with_a_task_graph(
    make_tool: Callable[..., ReannotateInstanceTool],
    t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
    task_graph: dict[str, MagicMock],
    capsys: pytest.CaptureFixture[str],
    study_ids: list[str],
    full_reannotation: bool,
) -> None:
    graphs = [MagicMock(name=study_id) for study_id in study_ids]
    task_graph["generate"].side_effect = graphs
    extra = ["-r", "1000", "-j", "1"]
    if full_reannotation:
        extra.append("--full-reannotation")
    tool = make_tool(*extra)

    tool.run()

    assert capsys.readouterr().out.splitlines()[0] == (
        "Studies to be reannotated:")
    generate_calls = task_graph["generate"].call_args_list
    assert [call.args for call in generate_calls] == [
        (
            t4c8_instance,
            str(pathlib.Path(t4c8_instance.dae_dir)
                / "duckdb_storage" / study_id),
            1000,
            tmp_path / "work" / study_id,
        )
        for study_id in study_ids
    ]
    assert all(
        call.kwargs == {
            "allow_repeated_attributes": False,
            "full_reannotation": full_reannotation,
        }
        for call in generate_calls
    )
    process_calls = task_graph["process"].call_args_list
    assert [call.args[0] for call in process_calls] == graphs
    for study_id, call in zip(study_ids, process_calls, strict=True):
        assert call.kwargs["task_status_dir"] == str(
            tmp_path / ".task-progress" / study_id)
        assert call.kwargs["task_log_dir"] == str(
            tmp_path / ".task-log" / study_id)
        assert call.kwargs["work_dir"] == str(tmp_path)
        assert call.kwargs["full_reannotation"] is full_reannotation
