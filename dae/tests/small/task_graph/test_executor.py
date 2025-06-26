# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import os
import pathlib
import time
from collections.abc import Generator

import pytest
from dae.task_graph.cache import FileTaskCache
from dae.task_graph.executor import (
    AbstractTaskGraphExecutor,
    DaskExecutor,
    SequentialExecutor,
)
from dae.task_graph.graph import TaskGraph
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


def test_dependancy_chain(executor: AbstractTaskGraphExecutor) -> None:
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

    graph.create_task("9", add_to_list, args=[9, last_task], deps=[])

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
        executor: AbstractTaskGraphExecutor, tmp_path: pathlib.Path) -> None:
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
