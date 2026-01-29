# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import operator
import time

import pytest
from dae.task_graph.cli_tools import (
    task_graph_run_with_results,
)
from dae.task_graph.executor import (
    TaskGraphExecutor,
)
from dae.task_graph.graph import TaskGraph


def do_work(timeout: float) -> None:
    if timeout != 0:
        time.sleep(timeout)


def double(x: int) -> int:
    return x * 2


def test_dependency_chain(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, args=[0.01], deps=[])
    graph.create_task("Task 2", do_work, args=[0], deps=[task_1])

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]
    assert ids_in_finish_order == ["Task 1", "Task 2"]


def test_multiple_dependancies(executor: TaskGraphExecutor) -> None:
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


def add_to_list(what: int, where: list[int]) -> list[int]:
    where.append(what)
    return where


def test_implicit_dependancies(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()

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


def test_error_handling(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, args=[0], deps=[])
    task_2 = graph.create_task("Task 2", raise_exception, args=[], deps=[])
    graph.create_task("Task 3", do_work, args=[0], deps=[task_1, task_2])

    with pytest.raises(ValueError, match="Task failed"):
        list(task_graph_run_with_results(
            graph, executor, keep_going=False,
        ))


def test_error_handling_keep_going(
    executor: TaskGraphExecutor,
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


def test_diamond_graph(executor: TaskGraphExecutor) -> None:
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


def return_5() -> int:
    return 5


def test_result_passing_chain(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()
    task_a = graph.create_task("A", return_5, args=[], deps=[])
    task_b = graph.create_task("B", operator.add, args=[task_a, 3], deps=[])
    graph.create_task("C", operator.mul, args=[task_b, 2], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert results["A"] == 5
    assert results["B"] == 8
    assert results["C"] == 16


def test_wide_parallel_execution(executor: TaskGraphExecutor) -> None:
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


def test_empty_graph(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()
    results = list(executor.execute(graph))
    assert len(results) == 0


def return_42() -> int:
    return 42


def test_single_task_graph(executor: TaskGraphExecutor) -> None:
    graph = TaskGraph()
    graph.create_task("Only", return_42, args=[], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert len(results) == 1
    assert results["Only"] == 42


def return_1_2() -> list[int]:
    return [1, 2]


def return_3_4() -> list[int]:
    return [3, 4]


def return_5_6() -> list[int]:
    return [5, 6]


def merge_lists(*lists: list[int]) -> list[int]:
    # Merge results
    result = []
    for lst in lists:
        result.extend(lst)
    return result


def test_complex_result_aggregation(
    executor: TaskGraphExecutor,
) -> None:
    # Test complex data flow with multiple branches merging
    graph = TaskGraph()

    # Create initial tasks that produce lists
    task_a = graph.create_task("A", return_1_2, args=[], deps=[])
    task_b = graph.create_task("B", return_3_4, args=[], deps=[])
    task_c = graph.create_task("C", return_5_6, args=[], deps=[])

    graph.create_task(
        "Merge", merge_lists, args=[task_a, task_b, task_c], deps=[])

    results = {
        task.task_id: result for task, result in executor.execute(graph)
    }

    assert results["A"] == [1, 2]
    assert results["B"] == [3, 4]
    assert results["C"] == [5, 6]
    assert results["Merge"] == [1, 2, 3, 4, 5, 6]
