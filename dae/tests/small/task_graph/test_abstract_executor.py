# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Generator
from typing import Any, cast

import networkx
import pytest
from dae.task_graph.base_executor import TaskGraphExecutorBase
from dae.task_graph.cache import (
    CacheRecord,
    CacheRecordType,
    FileTaskCache,
    TaskCache,
)
from dae.task_graph.cli_tools import (
    task_graph_all_done,
    task_graph_run,
    task_graph_run_with_results,
    task_graph_status,
)
from dae.task_graph.dask_executor import DaskExecutor
from dae.task_graph.executor import (
    TaskGraphExecutor,
)
from dae.task_graph.graph import Task, TaskGraph
from dae.task_graph.process_pool_executor import ProcessPoolTaskExecutor
from dae.task_graph.sequential_executor import SequentialExecutor
from dask.distributed import Client


@pytest.fixture
def dask_client() -> Generator[Client, None, None]:
    # The client needs to be threaded b/c the global ORDER variable is modified
    client = Client(n_workers=2, threads_per_worker=1, processes=False)
    yield client
    client.close()


@pytest.fixture(params=["dask", "sequential", "process_pool"])
def executor(
    dask_client: Client,
    request: pytest.FixtureRequest,
) -> TaskGraphExecutor:
    if request.param == "dask":
        return DaskExecutor(dask_client)
    if request.param == "process_pool":
        return ProcessPoolTaskExecutor()
    return SequentialExecutor()


def add_to_list(what: int, where: list[int]) -> list[int]:
    return [*where, what]


def concat_lists(*lists: list[int]) -> list[int]:
    res = []
    for next_list in lists:
        res.extend(next_list)
    return res


def _create_graph_with_result_passing() -> TaskGraph:

    # create the task graph
    graph = TaskGraph()
    first_task = graph.create_task("0", add_to_list, args=[0, []], deps=[])
    add_tasks = [
        graph.create_task(f"{i}", add_to_list, args=[i, first_task], deps=[])
        for i in range(1, 8)
    ]
    graph.create_task("final", concat_lists, args=add_tasks, deps=[])
    return graph


def raise_exception() -> None:
    raise ValueError("Task failed")


class DummyCache(TaskCache):
    def __init__(self, mapping: dict[Task, CacheRecord]):
        self.mapping = mapping

    def load(
        self, graph: TaskGraph,
    ) -> Generator[tuple[Task, CacheRecord], None, None]:
        for task in graph.tasks:
            yield task, self.mapping.get(
                task, CacheRecord(CacheRecordType.NEEDS_COMPUTE),
            )

    def cache(
        self, task_node: Task, *,
        is_error: bool, result: Any,
    ) -> None:
        record_type = (
            CacheRecordType.ERROR if is_error
            else CacheRecordType.COMPUTED
        )
        self.mapping[task_node] = CacheRecord(record_type, result)


def test_calling_execute_twice(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()
    first_task = graph.create_task("First", lambda: None, args=[], deps=[])
    second_layer_tasks = [
        graph.create_task(f"{i}", lambda: None, args=[], deps=[first_task])
        for i in range(10)
    ]
    graph.create_task("Third", lambda: None, args=[], deps=second_layer_tasks)

    # cannot execute a graph while executing another one
    tasks_iter = executor.execute(graph)
    next(tasks_iter)

    with pytest.raises(AssertionError):
        next(executor.execute(graph))

    # but ones the original is finished we can execute a new one
    list(tasks_iter)
    executor.execute(graph)


def test_executing_with_cache(
    executor: TaskGraphExecutor, tmp_path: pathlib.Path,
) -> None:
    graph = _create_graph_with_result_passing()
    base_executor = cast(TaskGraphExecutorBase, executor)
    # initial execution of the graph
    base_executor._task_cache = FileTaskCache(cache_dir=str(tmp_path))
    task_results = list(executor.execute(graph))
    assert len(task_results) == 9

    # now make a change and make sure the correct function with the correct
    # results are returned
    graph = _create_graph_with_result_passing()

    base_executor._task_cache = FileTaskCache(cache_dir=str(tmp_path))
    task_to_delete = graph.tasks[-2]
    assert task_to_delete.task_id == "7"
    os.remove(base_executor._task_cache._get_flag_filename(task_to_delete))

    task_results = list(executor.execute(graph))
    assert len(task_results) == 9
    for task, result in task_results:
        if task.task_id == "final":
            assert result == [0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7]


def test_task_graph_run_successful_execution(
    capsys: pytest.CaptureFixture,
) -> None:
    graph = TaskGraph()
    graph.create_task("simple", lambda: 1, args=[], deps=[])

    assert task_graph_run(graph) is True

    captured = capsys.readouterr()
    assert captured.err == ""


def test_task_graph_run_keep_going_logs_errors(
    capsys: pytest.CaptureFixture,
) -> None:
    graph = TaskGraph()
    graph.create_task("ok", lambda: 1, args=[], deps=[])
    graph.create_task("fail", raise_exception, args=[], deps=[])

    result = task_graph_run(graph, keep_going=True)

    assert result is False
    captured = capsys.readouterr()
    assert "Task fail failed with:" in captured.err
    assert "ValueError: Task failed" in captured.out


def test_task_graph_run_with_results_yields_values() -> None:
    def produce_one() -> int:
        return 1

    def add_one(value: int) -> int:
        return value + 1

    graph = TaskGraph()
    first = graph.create_task("first", produce_one, args=[], deps=[])
    graph.create_task("second", add_one, args=[first], deps=[first])

    assert list(task_graph_run_with_results(graph)) == [1, 2]


def test_task_graph_run_with_results_keep_going_handles_error(
    capsys: pytest.CaptureFixture,
) -> None:
    graph = TaskGraph()
    graph.create_task("ok", lambda: 1, args=[], deps=[])
    graph.create_task("fail", raise_exception, args=[], deps=[])

    results = list(task_graph_run_with_results(graph, keep_going=True))

    assert len(results) == 2
    assert any(isinstance(r, ValueError) for r in results)

    captured = capsys.readouterr()
    assert "Task fail failed with:" in captured.err
    assert "ValueError: Task failed" in captured.out


def test_task_graph_status_prints_records(
    capsys: pytest.CaptureFixture,
) -> None:
    graph = TaskGraph()
    ok_task = graph.create_task("ok", lambda: None, args=[], deps=[])
    fail_task = graph.create_task("fail", lambda: None, args=[], deps=[])

    cache = DummyCache({
        ok_task: CacheRecord(CacheRecordType.COMPUTED, "done"),
        fail_task: CacheRecord(
            CacheRecordType.ERROR, ValueError("status failure"),
        ),
    })

    assert task_graph_status(graph, cache, verbose=0) is True

    captured = capsys.readouterr()
    assert "TaskID" in captured.out
    assert "COMPUTED" in captured.out
    assert "ERROR" in captured.out
    assert "(-v to see exception)" in captured.out
    assert "ValueError" not in captured.out


def test_task_graph_status_verbose_prints_traceback(
    capsys: pytest.CaptureFixture,
) -> None:
    graph = TaskGraph()
    ok_task = graph.create_task("ok", lambda: None, args=[], deps=[])
    fail_task = graph.create_task("fail", lambda: None, args=[], deps=[])

    cache = DummyCache({
        ok_task: CacheRecord(CacheRecordType.COMPUTED, "done"),
        fail_task: CacheRecord(
            CacheRecordType.ERROR, ValueError("status failure"),
        ),
    })

    assert task_graph_status(graph, cache, verbose=1) is True

    captured = capsys.readouterr()
    assert "ValueError: status failure" in captured.out
    assert "(-v to see exception)" not in captured.out


def test_task_graph_all_done_returns_true_when_all_computed() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])

    cache = DummyCache({
        task_a: CacheRecord(CacheRecordType.COMPUTED, None),
        task_b: CacheRecord(CacheRecordType.COMPUTED, None),
    })

    assert task_graph_all_done(graph, cache) is True


def test_task_graph_all_done_returns_false_when_missing_results() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])

    cache = DummyCache({
        task_a: CacheRecord(CacheRecordType.COMPUTED, None),
        task_b: CacheRecord(CacheRecordType.NEEDS_COMPUTE, None),
    })

    assert task_graph_all_done(graph, cache) is False


def test_task_graph_all_done_detects_cycle() -> None:
    graph = TaskGraph()
    graph.create_task("A", lambda: None, args=[], deps=[Task("B")])
    graph.create_task("B", lambda: None, args=[], deps=[Task("A")])

    cache = DummyCache({})

    with pytest.raises(ValueError, match="Cyclic dependency"):
        task_graph_all_done(graph, cache)


@pytest.mark.parametrize(
    "tasks,expected_order", [
        (
            # initial
            [
                ("2", []),
                ("3", []),
                ("1", ["2", "3"]),
            ],
            ["2", "3", "1"],
        ),
        (
            # different order
            [
                ("3", []),
                ("2", []),
                ("1", ["2", "3"]),
            ],
            ["3", "2", "1"],
        ),
        (
            # simple chain
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["B"]),
            ],
            ["A", "B", "C"],
        ),
        (
            # 2 chains
            [
                ("A1", []),
                ("B1", ["A1"]),
                ("C1", ["B1"]),
                ("A2", []),
                ("B2", ["A2"]),
                ("C2", ["B2"]),
            ],
            ["A1", "A2", "B1", "B2", "C1", "C2"],
        ),
        (
            # 2 deeper chains
            [
                ("A1", []),
                ("B1", ["A1"]),
                ("C1", ["B1"]),
                ("D1", ["C1"]),
                ("A2", []),
                ("B2", ["A2"]),
                ("C2", ["B2"]),
                ("D2", ["C2"]),
            ],
            ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2"],
        ),

    ],
)
def test_topological_sort(
    tasks: list[tuple[str, list[str]]],
    expected_order: list[str],
) -> None:
    graph = networkx.DiGraph()
    for task_id, _dep_ids in tasks:
        graph.add_node(task_id)
    for task_id, dep_ids in tasks:
        for dep_id in dep_ids:
            graph.add_edge(dep_id, task_id)
    assert networkx.is_directed_acyclic_graph(graph)
    result = list(networkx.topological_sort(graph))
    assert result == expected_order
