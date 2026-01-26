# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613,too-many-lines
import argparse
import pathlib
import pickle  # noqa: S403
from collections.abc import Callable
from typing import Any, cast

import fsspec
import pytest
from dae.task_graph import TaskGraph, TaskGraphCli
from dae.task_graph.base_executor import TaskGraphExecutorBase


def add_to_list(what: int, where: list[int]) -> list[int]:
    where.append(what)
    return where


def test_executor_fork_tasks(
    tmp_path: pathlib.Path,
) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser, task_progress_mode=True)
    args = parser.parse_args(
        ["--fork-tasks", "-j", "1", "-f", "-d", str(tmp_path)])
    executor = TaskGraphCli.create_executor(**vars(args))
    assert executor

    graph = TaskGraph()

    graph.create_task("0", add_to_list, args=[0, []], deps=[])

    TaskGraphCli.process_graph(graph, **vars(args))

    assert (tmp_path / "0.result").exists()


def test_exec_without_fork_invokes_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_internal(
        task_func: Callable[..., object],
        args: list[object],
        params: dict[str, object],
    ) -> str:
        captured["call"] = (task_func, args, params)
        return "sentinel"

    monkeypatch.setattr(
        TaskGraphExecutorBase,
        "_exec_internal",
        staticmethod(fake_internal),
    )

    def sample_task(value: int) -> int:
        return value * 2

    params = {"fork_tasks": False, "task_id": "plain"}

    result = TaskGraphExecutorBase._exec(
        sample_task, [21], params,
    )

    assert result == "sentinel"
    assert captured["call"] == (sample_task, [21], params)


def test_exec_with_fork_uses_process_and_reads_result(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, Any] = {}

    def fake_internal(
        task_func: Callable[..., object],
        args: list[object],
        params: dict[str, object],
    ) -> dict[str, int]:
        calls["internal"] = (task_func, args, params)
        return {"value": 42}

    monkeypatch.setattr(
        TaskGraphExecutorBase,
        "_exec_internal",
        staticmethod(fake_internal),
    )

    class FakeProcess:
        def __init__(self, *init_args: object, **init_kwargs: object) -> None:
            assert not init_args
            self._target = cast(Callable, init_kwargs["target"])
            self._args = cast(list[object], init_kwargs["args"])
            calls["init"] = True

        def start(self) -> None:
            calls["start"] = True
            self._target(*self._args)

        def join(self) -> None:
            calls["join"] = True

    monkeypatch.setattr(
        "dae.task_graph.base_executor.mp.Process",
        FakeProcess,
    )

    params = {
        "fork_tasks": True,
        "task_id": "forked",
        "task_status_dir": str(tmp_path),
    }

    result = TaskGraphExecutorBase._exec(
        add_to_list, [5, []], params,
    )

    assert calls.get("init")
    assert calls.get("start")
    assert calls.get("join")
    assert calls["internal"][2] == params
    assert result == {"value": 42}
    assert (tmp_path / "forked.result").exists()


def test_exec_forked_simple(
    tmp_path: pathlib.Path,
) -> None:

    TaskGraphExecutorBase._exec_forked(
        add_to_list, args=[1, []],
        params={"task_id": "0", "task_status_dir": str(tmp_path)},
    )

    result_fn = TaskGraphExecutorBase._result_fn(
        {"task_id": "0", "task_status_dir": str(tmp_path)})
    assert pathlib.Path(result_fn).exists()
    with fsspec.open(result_fn, "rb") as infile:
        result = pickle.load(infile)  # pyright: ignore
    assert result == [1]


def test_exec_forked_exception(
    tmp_path: pathlib.Path,
) -> None:

    def raise_exception() -> None:
        raise ValueError("Test exception")

    TaskGraphExecutorBase._exec_forked(
        raise_exception, args=[],
        params={"task_id": "0", "task_status_dir": str(tmp_path)},
    )

    result_fn = TaskGraphExecutorBase._result_fn(
        {"task_id": "0", "task_status_dir": str(tmp_path)})
    assert pathlib.Path(result_fn).exists()
    with fsspec.open(result_fn, "rb") as infile:
        result = pickle.load(infile)  # pyright: ignore
    assert isinstance(result, ValueError)
    assert str(result) == "Test exception"
