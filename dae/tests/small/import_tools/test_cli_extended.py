# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Extended tests for import_tools.cli module."""
import pathlib
import shutil
import sys
from typing import Any

import pytest
import pytest_mock
import yaml
from dae.genomic_resources.genomic_context import GenomicContext
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools import cli, import_tools
from dae.task_graph.executor import SequentialExecutor
from dae.testing.alla_import import alla_gpf


@pytest.fixture
def gpf_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(__name__)
    return alla_gpf(root_path)


@pytest.fixture
def simple_study_dir(
    tmp_path: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
    resources_dir: pathlib.Path,
) -> pathlib.Path:
    shutil.copytree(
        resources_dir / "vcf_import", tmp_path, dirs_exist_ok=True,
    )

    # copying to hdfs and impala is too slow so we remove that step
    config_fn = str(tmp_path / "import_config.yaml")
    with open(config_fn, "rt", encoding="utf-8") as file:
        config = yaml.safe_load(file.read())
    config["destination"] = {
        "id": "genotype_inmemory",
        "storage_type": "inmemory",
        "dir": str(tmp_path),
    }  # don't import into impala
    with open(config_fn, "wt", encoding="utf-8") as file:
        yaml.safe_dump(config, file)

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)
    mocker.patch.object(
        import_tools.ImportProject, "work_dir",
        new=str(tmp_path))
    return tmp_path


def test_main_with_none_argv(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
) -> None:
    """Test main() when called with argv=None (uses sys.argv)."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")
    # Mock sys.argv
    original_argv = sys.argv
    try:
        sys.argv = ["import_genotypes", import_config_fn, "-j", "1"]
        result = cli.main(None)
        assert result == 0
    finally:
        sys.argv = original_argv


def test_main_deprecated_tool_warning(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that deprecated tool names trigger a warning."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")
    logger_mock = mocker.patch("dae.import_tools.cli.logger")

    original_argv = sys.argv
    try:
        sys.argv = ["old_import_tool", import_config_fn, "-j", "1"]
        result = cli.main(None)
        # Should log a warning about deprecated tool
        logger_mock.warning.assert_called_once()
        assert "deprecated" in logger_mock.warning.call_args[0][0].lower()
        assert result == 0
    finally:
        sys.argv = original_argv


def test_main_with_explicit_task_status_dir(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    tmp_path: pathlib.Path,
) -> None:
    """Test main() with explicit task_status_dir argument."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")
    task_status_dir = str(tmp_path / "custom_task_status")

    result = cli.main([
        import_config_fn,
        "-j", "1",
        "--task-status-dir", task_status_dir,
    ])
    assert result == 0
    # Task status dir should have been used
    assert pathlib.Path(task_status_dir).exists()


def test_main_with_explicit_task_log_dir(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    tmp_path: pathlib.Path,
) -> None:
    """Test main() with explicit task_log_dir argument."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")
    task_log_dir = str(tmp_path / "custom_task_log")

    result = cli.main([
        import_config_fn,
        "-j", "1",
        "--task-log-dir", task_log_dir,
    ])
    assert result == 0


def test_main_default_task_status_dir_creation(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that default task_status_dir is created correctly."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    # Mock to intercept the args and check task_status_dir
    original_process_graph = cli.TaskGraphCli.process_graph
    called_args = {}

    def mock_process_graph(task_graph: Any, **kwargs: Any) -> bool:
        called_args.update(kwargs)
        return original_process_graph(task_graph, **kwargs)

    mocker.patch.object(
        cli.TaskGraphCli, "process_graph",
        side_effect=mock_process_graph)

    result = cli.main([import_config_fn, "-j", "1"])
    assert result == 0

    # Check that task_status_dir was set to the default path
    assert "task_status_dir" in called_args
    assert ".task-progress" in called_args["task_status_dir"]
    assert "test_import" in called_args["task_status_dir"]


def test_main_default_task_log_dir_creation(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that default task_log_dir is created correctly."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    # Mock to intercept the args
    original_process_graph = cli.TaskGraphCli.process_graph
    called_args = {}

    def mock_process_graph(task_graph: Any, **kwargs: Any) -> bool:
        called_args.update(kwargs)
        return original_process_graph(task_graph, **kwargs)

    mocker.patch.object(
        cli.TaskGraphCli, "process_graph",
        side_effect=mock_process_graph)

    result = cli.main([import_config_fn, "-j", "1"])
    assert result == 0

    # Check that task_log_dir was set to the default path
    assert "task_log_dir" in called_args
    assert ".task-log" in called_args["task_log_dir"]
    assert "test_import" in called_args["task_log_dir"]


def test_main_returns_1_on_failure(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that main() returns 1 when TaskGraphCli.process_graph fails."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    # Mock process_graph to return False (failure)
    mocker.patch.object(
        cli.TaskGraphCli, "process_graph",
        return_value=False)

    result = cli.main([import_config_fn, "-j", "1"])
    assert result == 1


def test_main_config_filenames_added_to_task_graph(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that config filenames are added to task graph input files."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    captured_task_graph = {}

    def mock_process_graph(task_graph: Any, **_kwargs: Any) -> bool:
        captured_task_graph["graph"] = task_graph
        return True

    mocker.patch.object(
        cli.TaskGraphCli, "process_graph",
        side_effect=mock_process_graph)

    result = cli.main([import_config_fn, "-j", "1"])
    assert result == 0

    # Check that config filename was added to input_files
    assert "graph" in captured_task_graph
    task_graph = captured_task_graph["graph"]
    assert import_config_fn in task_graph.input_files


def test_main_with_verbosity_arguments(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
) -> None:
    """Test main() with verbosity arguments."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    result = cli.main([import_config_fn, "-j", "1", "-v"])
    assert result == 0

    result = cli.main([import_config_fn, "-j", "1", "--verbose"])
    assert result == 0


def test_main_list_command_verbose(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
) -> None:
    """Test list command with verbose flag."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    result = cli.main([import_config_fn, "list", "-v"])
    assert result == 0


def test_run_with_project_default_executor(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test run_with_project() with default executor."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    result = cli.run_with_project(project)
    assert result is True


def test_run_with_project_custom_executor(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test run_with_project() with custom executor."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    custom_executor = SequentialExecutor()
    result = cli.run_with_project(project, executor=custom_executor)
    assert result is True


def test_run_with_project_adds_config_filenames(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that run_with_project adds config filenames to task graph."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    captured_task_graph = {}

    original_task_graph_run = cli.task_graph_run

    def mock_task_graph_run(
        task_graph: Any,
        executor: Any,
        *,
        keep_going: bool = False,
    ) -> bool:
        captured_task_graph["graph"] = task_graph
        return original_task_graph_run(
            task_graph, executor, keep_going=keep_going)

    mocker.patch(
        "dae.import_tools.cli.task_graph_run",
        side_effect=mock_task_graph_run)

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    result = cli.run_with_project(project)
    assert result is True

    # Check that config filenames were added
    assert "graph" in captured_task_graph
    task_graph = captured_task_graph["graph"]
    assert import_config_fn in task_graph.input_files


def test_run_with_project_uses_sequential_executor_by_default(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that run_with_project uses SequentialExecutor by default."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    captured_executor = {}

    original_task_graph_run = cli.task_graph_run

    def mock_task_graph_run(
        task_graph: Any,
        executor: Any,
        *,
        keep_going: bool = False,
    ) -> bool:
        captured_executor["executor"] = executor
        return original_task_graph_run(
            task_graph, executor, keep_going=keep_going)

    mocker.patch(
        "dae.import_tools.cli.task_graph_run",
        side_effect=mock_task_graph_run)

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    cli.run_with_project(project)

    # Check that SequentialExecutor was used
    assert "executor" in captured_executor
    assert isinstance(captured_executor["executor"], SequentialExecutor)


def test_run_with_project_keep_going_false(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that run_with_project calls task_graph_run with keep_going=False."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    captured_kwargs = {}

    original_task_graph_run = cli.task_graph_run

    def mock_task_graph_run(
        task_graph: Any,
        executor: Any,
        *,
        keep_going: bool = False,
    ) -> bool:
        captured_kwargs["keep_going"] = keep_going
        return original_task_graph_run(
            task_graph, executor, keep_going=keep_going)

    mocker.patch(
        "dae.import_tools.cli.task_graph_run",
        side_effect=mock_task_graph_run)

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    cli.run_with_project(project)

    # Check that keep_going was False
    assert "keep_going" in captured_kwargs
    assert captured_kwargs["keep_going"] is False


def test_main_with_help_argument() -> None:
    """Test that main() with --help exits gracefully."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])
    assert exc_info.value.code == 0


def test_main_missing_config_argument() -> None:
    """Test that main() without config argument fails."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main([])
    assert exc_info.value.code != 0


def test_run_with_project_returns_false_on_failure(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that run_with_project returns False when task_graph_run fails."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    # Mock task_graph_run to return False
    mocker.patch(
        "dae.import_tools.cli.task_graph_run",
        return_value=False)

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    result = cli.run_with_project(project)
    assert result is False


def test_main_creates_import_storage(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that main() creates import storage and generates task graph."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    get_import_storage_spy = mocker.spy(
        import_tools.ImportProject, "get_import_storage")

    result = cli.main([import_config_fn, "-j", "1"])
    assert result == 0

    # Verify get_import_storage was called
    assert get_import_storage_spy.call_count >= 1


def test_run_with_project_creates_import_storage(
    simple_study_dir: pathlib.Path,
    gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test that run_with_project creates import storage."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    mocker.patch.object(
        import_tools.ImportProject, "get_gpf_instance",
        return_value=gpf_instance)

    get_import_storage_spy = mocker.spy(
        import_tools.ImportProject, "get_import_storage")

    project = import_tools.ImportProject.build_from_file(import_config_fn)
    cli.run_with_project(project)

    # Verify get_import_storage was called
    assert get_import_storage_spy.call_count >= 1


def test_main_with_parallel_jobs(
    simple_study_dir: pathlib.Path,
    context_fixture: GenomicContext,  # noqa: ARG001
) -> None:
    """Test main() with parallel jobs argument."""
    import_config_fn = str(simple_study_dir / "import_config.yaml")

    result = cli.main([import_config_fn, "-j", "2"])
    assert result == 0
