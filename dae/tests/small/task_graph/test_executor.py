# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import operator
import os
import pathlib
import time
from collections.abc import Generator
from typing import Any

import networkx
import pytest
from dae.task_graph.cache import (
    CacheRecord,
    CacheRecordType,
    FileTaskCache,
    TaskCache,
)
from dae.task_graph.executor import (
    AbstractTaskGraphExecutor,
    DaskExecutor,
    SequentialExecutor,
    task_graph_all_done,
    task_graph_run,
    task_graph_run_with_results,
    task_graph_status,
)
from dae.task_graph.graph import Task, TaskGraph
from dask.distributed import Client


@pytest.fixture(scope="module")
def threaded_client() -> Generator[Client, None, None]:
    # The client needs to be threaded b/c the global ORDER variable is modified
    client = Client(n_workers=4, threads_per_worker=1, processes=False)
    yield client
    client.close()


@pytest.fixture(params=["dask", "sequential"])
def executor(
        threaded_client: Client,
        request: pytest.FixtureRequest) -> AbstractTaskGraphExecutor:
    if request.param == "dask":
        return DaskExecutor(threaded_client)
    return SequentialExecutor()


def do_work(timeout: float) -> None:
    if timeout != 0:
        time.sleep(timeout)


def double(x: int) -> int:
    return x * 2


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


def test_dependency_chain(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, args=[0.01], deps=[])
    graph.create_task("Task 2", do_work, args=[0], deps=[task_1])

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]
    assert ids_in_finish_order == ["Task 1", "Task 2"]


def test_multiple_dependancies(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()

    tasks = []
    for i in range(10):
        task = graph.create_task(f"Task {i}", do_work, args=[0], deps=[])
        tasks.append(task)

    for i in range(100, 105):
        graph.create_task(f"Task {i}", do_work, args=[0], deps=tasks)

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]

    assert len(ids_in_finish_order) == 15


def test_implicit_dependancies(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()

    def add_to_list(what: int, where: list[int]) -> list[int]:
        where.append(what)
        return where

    last_task = graph.create_task("0", add_to_list, args=[0, []], deps=[])
    for i in range(1, 9):
        last_task = graph.create_task(
            f"{i}", add_to_list, args=[i, last_task], deps=[])

    last_task = graph.create_task(
        "9", add_to_list, args=[9, last_task], deps=[])

    full_list = []
    for task, result in executor.execute(graph):
        print(task, result)
        if task == last_task:
            full_list = result

    assert full_list == list(range(10))


def test_calling_execute_twice(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    first_task = graph.create_task("First", lambda: None, args=[], deps=[])
    second_layer_tasks = [
        graph.create_task(f"{i}", lambda: None, args=[], deps=[first_task])
        for i in range(10)
    ]
    graph.create_task("Third", lambda: None, args=[], deps=second_layer_tasks)

    # cannot execute a graph while executing another one
    tasks_iter = executor.execute(graph)
    with pytest.raises(AssertionError):
        executor.execute(graph)

    # but ones the original is finished we can execute a new one
    list(tasks_iter)
    executor.execute(graph)


def test_executing_with_cache(
    executor: AbstractTaskGraphExecutor, tmp_path: pathlib.Path,
) -> None:
    graph = _create_graph_with_result_passing()

    # initial execution of the graph
    executor._task_cache = FileTaskCache(cache_dir=str(tmp_path))
    task_results = list(executor.execute(graph))
    assert len(task_results) == 9

    # now make a change and make sure the correct function with the correct
    # results are returned
    executor._task_cache = FileTaskCache(cache_dir=str(tmp_path))
    task_to_delete = graph.tasks[-2]
    assert task_to_delete.task_id == "7"
    os.remove(executor._task_cache._get_flag_filename(task_to_delete))

    task_results = list(executor.execute(graph))
    assert len(task_results) == 9
    for task, result in task_results:
        if task.task_id == "final":
            assert result == [0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7]


def _create_graph_with_result_passing() -> TaskGraph:
    def add_to_list(what: int, where: list[int]) -> list[int]:
        return [*where, what]

    def concat_lists(*lists: list[int]) -> list[int]:
        res = []
        for next_list in lists:
            res.extend(next_list)
        return res

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


def test_error_handling(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, args=[0], deps=[])
    task_2 = graph.create_task("Task 2", raise_exception, args=[], deps=[])
    graph.create_task("Task 3", do_work, args=[0], deps=[task_1, task_2])

    with pytest.raises(ValueError, match="Task failed"):
        list(task_graph_run_with_results(
            graph, executor, keep_going=False,
        ))


def test_error_handling_keep_going(
    executor: AbstractTaskGraphExecutor,
) -> None:
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, args=[0], deps=[])
    task_2 = graph.create_task("Task 2", raise_exception, args=[], deps=[])
    graph.create_task("Task 3", do_work, args=[0], deps=[task_1])
    graph.create_task("Task 4", do_work, args=[0], deps=[task_2])

    results = list(executor.execute(graph))
    assert len(results) == 3

    error_tasks = []
    ok_tasks = []
    for task, result in results:
        if isinstance(result, ValueError):
            error_tasks.append(task.task_id)
        else:
            ok_tasks.append(task.task_id)

    assert "Task 2" in error_tasks
    assert "Task 1" in ok_tasks
    assert "Task 3" in ok_tasks
    assert "Task 4" not in ok_tasks
    assert "Task 4" not in error_tasks


def test_diamond_graph(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", do_work, args=[0.01], deps=[])
    task_b = graph.create_task("B", do_work, args=[0.01], deps=[task_a])
    task_c = graph.create_task("C", do_work, args=[0.01], deps=[task_a])
    graph.create_task("D", do_work, args=[0.01], deps=[task_b, task_c])

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]

    assert len(ids_in_finish_order) == 4
    assert ids_in_finish_order[0] == "A"
    assert set(ids_in_finish_order[1:3]) == {"B", "C"}
    assert ids_in_finish_order[3] == "D"


def test_result_passing_chain(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: 5, args=[], deps=[])
    task_b = graph.create_task("B", operator.add, args=[task_a, 3], deps=[])
    graph.create_task("C", operator.mul, args=[task_b, 2], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert results["A"] == 5
    assert results["B"] == 8
    assert results["C"] == 16


def test_wide_parallel_execution(executor: AbstractTaskGraphExecutor) -> None:
    # Test many independent tasks that can run in parallel
    graph = TaskGraph()
    num_tasks = 50

    for i in range(num_tasks):
        graph.create_task(f"WideTask{i}", double, args=[i], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert len(results) == num_tasks
    for i in range(num_tasks):
        assert results[f"WideTask{i}"] == i * 2


def test_empty_graph(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    results = list(executor.execute(graph))
    assert len(results) == 0


def test_single_task_graph(executor: AbstractTaskGraphExecutor) -> None:
    graph = TaskGraph()
    graph.create_task("Only", lambda: 42, args=[], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert len(results) == 1
    assert results["Only"] == 42


def test_complex_result_aggregation(
    executor: AbstractTaskGraphExecutor,
) -> None:
    # Test complex data flow with multiple branches merging
    graph = TaskGraph()

    # Create initial tasks that produce lists
    task_a = graph.create_task("A", lambda: [1, 2], args=[], deps=[])
    task_b = graph.create_task("B", lambda: [3, 4], args=[], deps=[])
    task_c = graph.create_task("C", lambda: [5, 6], args=[], deps=[])

    # Merge results
    def merge_lists(*lists: list[int]) -> list[int]:
        result = []
        for lst in lists:
            result.extend(lst)
        return result

    graph.create_task(
        "Merge", merge_lists, args=[task_a, task_b, task_c], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert results["A"] == [1, 2]
    assert results["B"] == [3, 4]
    assert results["C"] == [5, 6]
    assert results["Merge"] == [1, 2, 3, 4, 5, 6]


def test_check_for_cyclic_deps_allows_acyclic_graph() -> None:
    graph = TaskGraph()
    root = graph.create_task("root", lambda: None, args=[], deps=[])
    child = graph.create_task("child", lambda: None, args=[], deps=[root])
    graph.create_task("leaf", lambda: None, args=[], deps=[child])

    # Should not raise for acyclic graphs
    AbstractTaskGraphExecutor._check_for_cyclic_deps(graph)


def test_check_for_cyclic_deps_detects_cycle() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])

    # introduce a cycle A -> B -> A
    task_a.deps.append(task_b)

    with pytest.raises(ValueError, match="Cyclic dependency"):
        AbstractTaskGraphExecutor._check_for_cyclic_deps(graph)


def test_find_cycle_returns_none_for_acyclic_graph() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])
    graph.create_task("C", lambda: None, args=[], deps=[task_b])

    visited: set = set()
    cycle = AbstractTaskGraphExecutor._find_cycle(task_a, visited, [])

    assert cycle is None
    assert task_a in visited


def test_find_cycle_detects_simple_cycle() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])
    task_a.deps.append(task_b)

    cycle = AbstractTaskGraphExecutor._find_cycle(task_a, set(), [])

    assert cycle is not None
    assert [task.task_id for task in cycle] == ["A", "B"]


def test_find_cycle_detects_nested_cycle() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[])
    task_c = graph.create_task("C", lambda: None, args=[], deps=[])

    task_a.deps.append(task_b)
    task_b.deps.append(task_c)
    task_c.deps.append(task_b)  # creates cycle B -> C -> B downstream of A

    cycle = AbstractTaskGraphExecutor._find_cycle(task_a, set(), [])

    assert cycle is not None
    assert [task.task_id for task in cycle] == ["A", "B", "C"]


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
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])
    task_a.deps.append(task_b)

    cache = DummyCache({})

    with pytest.raises(ValueError, match="Cyclic dependency"):
        task_graph_all_done(graph, cache)


def test_walk_graph_wide_1() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    task_b = graph.create_task("B", lambda: None, args=[], deps=[task_a])
    task_c = graph.create_task("C", lambda: None, args=[], deps=[task_a])
    graph.create_task("D", lambda: None, args=[], deps=[task_b, task_c])

    tasks_in_walk_order = list(
        AbstractTaskGraphExecutor._toplogical_order(graph),
    )
    ids_in_walk_order = [task.task_id for task in tasks_in_walk_order]

    assert len(ids_in_walk_order) == 4
    assert ids_in_walk_order[0] == "A"
    assert set(ids_in_walk_order[1:3]) == {"B", "C"}
    assert ids_in_walk_order[3] == "D"


def test_walk_graph_wide_2() -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", lambda: None, args=[], deps=[])
    graph.create_task("B", lambda: None, args=[], deps=[task_a])
    graph.create_task("C", lambda: None, args=[], deps=[])
    graph.create_task("D", lambda: None, args=[], deps=[])

    tasks_in_walk_order = list(
        AbstractTaskGraphExecutor._toplogical_order(graph),
    )
    ids_in_walk_order = [task.task_id for task in tasks_in_walk_order]

    assert len(ids_in_walk_order) == 4
    assert ids_in_walk_order == ["A", "C", "D", "B"]


def test_walk_graph_wide_3() -> None:
    graph = TaskGraph()
    for i in range(5):
        task_a = graph.create_task(f"A{i}", lambda: None, args=[], deps=[])
        graph.create_task(
            f"B{i}", lambda: None, args=[], deps=[task_a])

    tasks_in_walk_order = list(
        AbstractTaskGraphExecutor._toplogical_order(graph),
    )
    ids_in_walk_order = [task.task_id for task in tasks_in_walk_order]

    assert len(ids_in_walk_order) == 10
    assert ids_in_walk_order == [
        "A0", "A1", "A2", "A3", "A4",
        "B0", "B1", "B2", "B3", "B4",
    ]


def test_walk_graph_wide_4() -> None:
    graph = TaskGraph()
    for i in range(5):
        task_a = graph.create_task(f"A{i}", lambda: None, args=[], deps=[])
        task_b = graph.create_task(
            f"B{i}", lambda: None, args=[], deps=[task_a])
        graph.create_task(
            f"C{i}", lambda: None, args=[], deps=[task_b])

    tasks_in_walk_order = list(
        AbstractTaskGraphExecutor._toplogical_order(graph),
    )
    ids_in_walk_order = [task.task_id for task in tasks_in_walk_order]

    assert len(ids_in_walk_order) == 15
    assert ids_in_walk_order == [
        "A0", "A1", "A2", "A3", "A4",
        "B0", "B1", "B2", "B3", "B4",
        "C0", "C1", "C2", "C3", "C4",
    ]


def test_walk_graph_wide_5() -> None:
    graph = TaskGraph()
    for i in range(5):
        task_a = graph.create_task(f"A{i}", lambda: None, args=[], deps=[])
        task_b = graph.create_task(
            f"B{i}", lambda: None, args=[], deps=[task_a])
        task_c = graph.create_task(
            f"C{i}", lambda: None, args=[], deps=[task_b])
        graph.create_task(
            f"D{i}", lambda: None, args=[], deps=[task_c])

    tasks_in_walk_order = list(
        AbstractTaskGraphExecutor._toplogical_order(graph),
    )
    ids_in_walk_order = [task.task_id for task in tasks_in_walk_order]

    assert len(ids_in_walk_order) == 20
    assert ids_in_walk_order == [
        "A0", "A1", "A2", "A3", "A4",
        "B0", "B1", "B2", "B3", "B4",
        "C0", "C1", "C2", "C3", "C4",
        "D0", "D1", "D2", "D3", "D4",
    ]


def test_walk_graph_wide_6() -> None:
    graph = TaskGraph()
    first_task = graph.create_task("A", lambda: None, args=[], deps=[])
    second_layer_tasks = [
        graph.create_task(f"B{i}", lambda: None, args=[], deps=[first_task])
        for i in range(5)
    ]
    intermediate_task = graph.create_task(
        "C4", lambda: None,
        args=[], deps=second_layer_tasks[-1:],  # just the last one
    )
    third_task = graph.create_task(
        "D", lambda: None, args=[],
        deps=[*second_layer_tasks, intermediate_task],
    )
    graph.create_task("E", lambda: None, args=[], deps=[third_task])
    ids_in_walk_order = [
        task.task_id
        for task in AbstractTaskGraphExecutor._toplogical_order(graph)]
    assert len(ids_in_walk_order) == 9
    assert ids_in_walk_order == [
        "A",
        "B0", "B1", "B2", "B3", "B4",
        "C4",
        "D",
        "E",
    ]


@pytest.mark.parametrize(
    "tasks,expected_order", [
        (  # simple chain
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["B"]),
            ],
            ["A", "B", "C"],
        ),
        (  # diamond
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B", "C"]),
            ],
            ["A", "B", "C", "D"],
        ),
        (  # wide graph
            [
                ("A", []),
                ("B", []),
                ("C", []),
                ("D", []),
                ("E", ["A", "B", "C", "D"]),
            ],
            ["A", "B", "C", "D", "E"],
        ),
        (  # complex graph
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["B", "C"]),
                ("F", ["D", "E"]),
            ],
            ["A", "B", "C", "D", "E", "F"],
        ),
        (
            [  # multiple roots
                ("A", []),
                ("B", []),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["C", "D"]),
            ],
            ["A", "B", "C", "D", "E"],
        ),
        (
            [  # multiple independent chains
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
            [
                ("3", []),
                ("2", []),
                ("1", ["2", "3"]),
            ],
            ["2", "3", "1"],
        ),
    ],
)
def test_walk_graph_wide(
    tasks: list[tuple[str, list[str]]],
    expected_order: list[str],
) -> None:
    graph = TaskGraph()
    task_map: dict[str, Task] = {}
    for task_id, dep_ids in tasks:
        deps = [task_map[dep_id] for dep_id in dep_ids]
        task = graph.create_task(task_id, lambda: None, args=[], deps=deps)
        task_map[task_id] = task

    tasks_in_walk_order = list(
        AbstractTaskGraphExecutor._toplogical_order(graph),
    )
    ids_in_walk_order = [task.task_id for task in tasks_in_walk_order]

    assert ids_in_walk_order == expected_order


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
