# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613,too-many-lines
import argparse
import pathlib
import pickle  # noqa: S403

import fsspec
import pytest
from dae.task_graph.base_executor import TaskGraphExecutorBase
from dae.task_graph.cli_tools import TaskGraphCli
from dae.task_graph.graph import Task, TaskDesc, TaskGraph


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


def sample_func(value: int) -> int:
    return value * 2


def fake_internal(
    task: TaskDesc,
    params: dict[str, object],
) -> str:
    task_func = task.func
    args = task.args
    params["call"] = (task_func, args, params)
    return "sentinel"


def test_exec_without_fork_invokes_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        TaskGraphExecutorBase,
        "_exec_internal",
        staticmethod(fake_internal),
    )

    params = {"fork_tasks": False, "task_id": "plain"}

    simple_task = TaskDesc(
        Task("test_task"),
        sample_func,
        [21],
        [],
        [],
    )
    result = TaskGraphExecutorBase._exec(
        simple_task, params,
    )

    assert result == "sentinel"
    assert params["call"] == (sample_func, [21], params)


def test_exec_forked_simple(
    tmp_path: pathlib.Path,
) -> None:

    task = TaskDesc(
        Task("test_task"),
        add_to_list,
        [1, []],
        [],
        [],
    )

    TaskGraphExecutorBase._exec_forked(
        task, params={"task_id": "0", "task_status_dir": str(tmp_path)},
    )

    result_fn = TaskGraphExecutorBase._result_fn(
        "test_task", {"task_status_dir": str(tmp_path)})
    assert pathlib.Path(result_fn).exists()
    with fsspec.open(result_fn, "rb") as infile:
        result = pickle.load(infile)  # pyright: ignore
    assert result == [1]


def raise_exception() -> None:
    raise ValueError("Test exception")


def test_exec_forked_exception(
    tmp_path: pathlib.Path,
) -> None:
    task = TaskDesc(
        Task("test_task"),
        raise_exception,
        [],
        [],
        [],
    )

    TaskGraphExecutorBase._exec_forked(
        task,
        params={"task_status_dir": str(tmp_path)},
    )

    result_fn = TaskGraphExecutorBase._result_fn(
        "test_task", {"task_status_dir": str(tmp_path)})
    assert pathlib.Path(result_fn).exists()
    with fsspec.open(result_fn, "rb") as infile:
        result = pickle.load(infile)  # pyright: ignore
    assert isinstance(result, ValueError)
    assert str(result) == "Test exception"
