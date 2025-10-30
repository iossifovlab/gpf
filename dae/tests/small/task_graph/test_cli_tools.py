# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613,too-many-lines
import argparse
from types import TracebackType
from typing import Any

import pytest
from dae.task_graph import (
    TaskGraph,
    TaskGraphCli,
)
from dae.task_graph import (
    cli_tools as cli_tools_module,
)


def test_basic_default_executor() -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args([])

    empty_graph = TaskGraph()
    TaskGraphCli.process_graph(empty_graph, **vars(args))


def test_basic_sequential_executor() -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(["-j", "1"])

    empty_graph = TaskGraph()
    TaskGraphCli.process_graph(empty_graph, **vars(args))


def test_task_progress_mode_disabled() -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser, task_progress_mode=False)
    args = parser.parse_args([])

    assert "force" not in vars(args)
    assert "task_status_dir" not in vars(args)


def test_task_progress_mode_enabled() -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(
        parser, task_progress_mode=True,
        default_task_status_dir="gosho")

    args = parser.parse_args([])
    assert not args.force
    assert args.task_status_dir == "gosho"

    args = parser.parse_args(["-d", "pesho"])
    assert not args.force
    assert args.task_status_dir == "pesho"

    args = parser.parse_args(["-f"])
    assert args.force
    assert args.task_status_dir == "gosho"


def test_process_graph_run_skips_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = TaskGraph()
    graph.create_task("a", lambda: None, args=[], deps=[])

    monkeypatch.setattr(
        cli_tools_module.TaskCache, "create",
        staticmethod(lambda **_kwargs: object()),
    )
    monkeypatch.setattr(
        cli_tools_module, "task_graph_all_done",
        lambda *_args: True,
    )

    def fail_create_executor(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("executor should not be created")

    monkeypatch.setattr(
        TaskGraphCli, "create_executor", staticmethod(fail_create_executor),
    )

    result = TaskGraphCli.process_graph(
        graph,
        command="run",
        keep_going=False,
        verbose=0,
        task_ids=None,
    )

    assert result is True


def test_process_graph_run_executes_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = TaskGraph()
    graph.create_task("a", lambda: None, args=[], deps=[])

    cache = object()
    monkeypatch.setattr(
        cli_tools_module.TaskCache, "create",
        staticmethod(lambda **_kwargs: cache),
    )
    monkeypatch.setattr(
        cli_tools_module, "task_graph_all_done",
        lambda *_args: False,
    )

    calls: dict[str, object] = {}

    class DummyExecutor:
        def __enter__(self) -> str:
            calls["entered"] = True
            return "executor"

        def __exit__(  # type: ignore
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            calls["exited"] = True
            return False

    monkeypatch.setattr(
        TaskGraphCli, "create_executor",
        staticmethod(lambda *_args, **_kwargs: DummyExecutor()),
    )

    def run_stub(
        task_graph: TaskGraph,
        executor: object,
        *,
        keep_going: bool,
    ) -> bool:
        calls["run"] = (task_graph, executor, keep_going)
        return True

    monkeypatch.setattr(
        cli_tools_module, "task_graph_run", run_stub,
    )

    result_bool = TaskGraphCli.process_graph(
        graph,
        command="run",
        keep_going=True,
        verbose=0,
        task_ids=None,
    )

    assert result_bool is True
    assert calls.get("entered")
    assert calls.get("exited")
    assert calls.get("run") == (graph, "executor", True)


@pytest.mark.parametrize("command", ["list", "status"])
def test_process_graph_reports_status(
    command: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = TaskGraph()
    graph.create_task("a", lambda: None, args=[], deps=[])

    cache = object()
    monkeypatch.setattr(
        cli_tools_module.TaskCache, "create",
        staticmethod(lambda **_kwargs: cache),
    )

    def raise_executor_created(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("executor should not be created")

    monkeypatch.setattr(
        TaskGraphCli,
        "create_executor",
        staticmethod(raise_executor_created),
    )

    def forbid_completion_check(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("should not check completion")

    monkeypatch.setattr(
        cli_tools_module,
        "task_graph_all_done",
        forbid_completion_check,
    )

    captured: dict[str, object] = {}

    def status_stub(
        task_graph: TaskGraph,
        cache_arg: object,
        verbose: int,
    ) -> bool:
        captured["args"] = (task_graph, cache_arg, verbose)
        return True

    monkeypatch.setattr(
        cli_tools_module, "task_graph_status", status_stub,
    )

    result_bool = TaskGraphCli.process_graph(
        graph,
        command=command,
        verbose=5,
        task_ids=None,
    )

    assert result_bool is True
    assert captured.get("args") == (graph, cache, 5)


def test_process_graph_prunes_requested_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = TaskGraph()
    graph.create_task("keep", lambda: None, args=[], deps=[])
    replacement_graph = TaskGraph()
    replacement_graph.create_task("keep", lambda: None, args=[], deps=[])

    prune_calls: list[list[str]] = []

    def prune_stub(ids_to_keep: list[str]) -> TaskGraph:
        prune_calls.append(list(ids_to_keep))
        return replacement_graph

    graph.prune = prune_stub  # type: ignore

    cache = object()
    monkeypatch.setattr(
        cli_tools_module.TaskCache, "create",
        staticmethod(lambda **_kwargs: cache),
    )
    monkeypatch.setattr(
        cli_tools_module, "task_graph_all_done",
        lambda *_args: False,
    )

    run_calls: list[tuple] = []

    def run_stub(
        task_graph: TaskGraph,
        executor: object,
        *,
        keep_going: bool,
    ) -> bool:
        run_calls.append((task_graph, executor, keep_going))
        return True

    class DummyExecutor:
        def __enter__(self) -> str:
            return "executor"

        def __exit__(  # type: ignore
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

    monkeypatch.setattr(
        TaskGraphCli, "create_executor",
        staticmethod(lambda *_args, **_kwargs: DummyExecutor()),
    )
    monkeypatch.setattr(
        cli_tools_module, "task_graph_run", run_stub,
    )

    result_bool = TaskGraphCli.process_graph(
        graph,
        command="run",
        task_ids=["keep"],
        keep_going=False,
        verbose=0,
    )

    assert result_bool is True
    assert prune_calls == [["keep"]]
    assert run_calls == [(replacement_graph, "executor", False)]


def test_process_graph_unknown_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = TaskGraph()
    graph.create_task("a", lambda: None, args=[], deps=[])

    monkeypatch.setattr(
        cli_tools_module.TaskCache, "create",
        staticmethod(lambda **_kwargs: object()),
    )

    with pytest.raises(ValueError, match="Unknown command"):
        TaskGraphCli.process_graph(
            graph,
            command="not-a-command",
            verbose=0,
            task_ids=None,
        )
