# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import argparse
import pathlib
import pickle  # noqa: S403

import fsspec
from dae.task_graph import TaskGraph, TaskGraphCli
from dae.task_graph.executor import AbstractTaskGraphExecutor


def add_to_list(what: int, where: list[int]) -> list[int]:
    where.append(what)
    return where


def test_executor_fork_worker(
    tmp_path: pathlib.Path,
) -> None:
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser, task_progress_mode=True)
    args = parser.parse_args(
        ["--fork-worker", "-j", "1", "-f", "-d", str(tmp_path)])
    executor = TaskGraphCli.create_executor(**vars(args))
    assert executor

    graph = TaskGraph()

    graph.create_task("0", add_to_list, args=[0, []], deps=[])

    TaskGraphCli.process_graph(graph, **vars(args))

    assert (tmp_path / "0.result").exists()


def test_exec_forked_simple(
    tmp_path: pathlib.Path,
) -> None:

    AbstractTaskGraphExecutor._exec_forked(
        add_to_list, args=[1, []], deps=[],
        params={"task_id": "0", "task_status_dir": str(tmp_path)},
    )

    result_fn = AbstractTaskGraphExecutor._result_fn(
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

    AbstractTaskGraphExecutor._exec_forked(
        raise_exception, args=[], deps=[],
        params={"task_id": "0", "task_status_dir": str(tmp_path)},
    )

    result_fn = AbstractTaskGraphExecutor._result_fn(
        {"task_id": "0", "task_status_dir": str(tmp_path)})
    assert pathlib.Path(result_fn).exists()
    with fsspec.open(result_fn, "rb") as infile:
        result = pickle.load(infile)  # pyright: ignore
    assert isinstance(result, ValueError)
    assert str(result) == "Test exception"
