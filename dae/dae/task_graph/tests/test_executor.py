# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import os
import time
import pytest

from dask.distributed import Client  # type: ignore

from dae.task_graph.cache import FileTaskCache
from dae.task_graph.graph import TaskGraph
from dae.task_graph.executor import \
    DaskExecutor, SequentialExecutor


@pytest.fixture(scope="module")
def threaded_client():
    # The client needs to be threaded b/c the global ORDER variable is modified
    client = Client(n_workers=4, threads_per_worker=1, processes=False)
    yield client
    client.close()


@pytest.fixture(params=["dask", "sequential"])
def executor(threaded_client, request):
    if request.param == "dask":
        return DaskExecutor(threaded_client)
    return SequentialExecutor()


def do_work(timeout):
    if timeout != 0:
        time.sleep(timeout)


def test_dependancy_chain(executor):
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, [0.01], [])
    graph.create_task("Task 2", do_work, [0], [task_1])

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]
    assert ids_in_finish_order == ["Task 1", "Task 2"]


def test_multiple_dependancies(executor):
    graph = TaskGraph()

    tasks = []
    for i in range(10):
        task = graph.create_task(f"Task {i}", do_work, [0], [])
        tasks.append(task)

    for i in range(100, 105):
        graph.create_task(f"Task {i}", do_work, [0], tasks)

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]

    assert len(ids_in_finish_order) == 15
    assert set(ids_in_finish_order[:10]) == set(
        f"Task {i}" for i in range(10)
    )
    assert set(ids_in_finish_order[10:]) == set(
        f"Task {i}" for i in range(100, 105)
    )


def test_implicit_dependancies(executor):
    graph = TaskGraph()

    def add_to_list(what, where):
        where.append(what)
        return where

    last_task = graph.create_task("0", add_to_list, [0, []], [])
    for i in range(1, 8):
        last_task = graph.create_task(f"{i}", add_to_list, [i, last_task], [])

    graph.create_task("8", add_to_list, [8, last_task], [])

    tasks_in_finish_order = [task for task, _ in executor.execute(graph)]
    ids_in_finish_order = [task.task_id for task in tasks_in_finish_order]

    assert ids_in_finish_order == [f"{i}" for i in range(9)]


def test_active_tasks(executor):
    def noop():
        pass

    graph = TaskGraph()
    first_task = graph.create_task("First", noop, [], [])
    second_layer_tasks = [
        graph.create_task(f"Second {i}", noop, [], [first_task])
        for i in range(10)
    ]
    third_task = graph.create_task("Third", noop, [], second_layer_tasks)
    final_task = graph.create_task("Fourth", noop, [], [third_task])

    tasks_as_complete = executor.execute(graph)
    assert executor.get_active_tasks() == [first_task]
    assert next(tasks_as_complete)[0] is first_task

    for _ in range(10):
        assert set(executor.get_active_tasks()).issubset(second_layer_tasks)
        assert next(tasks_as_complete)[0] in second_layer_tasks
    assert executor.get_active_tasks() == [third_task]

    assert next(tasks_as_complete)[0] is third_task
    assert executor.get_active_tasks() == [final_task]
    assert next(tasks_as_complete)[0] is final_task
    assert len(executor.get_active_tasks()) == 0


def test_executing_with_cache(executor, tmpdir):
    graph = _create_graph_with_result_passing()

    # initial execution of the graph
    executor._task_cache = FileTaskCache(work_dir=tmpdir)
    task_results = list(executor.execute(graph))
    assert len(task_results) == 9

    # now make a change and make sure the correct function with the correct
    # results are returned
    executor._task_cache = FileTaskCache(work_dir=tmpdir)
    task_to_delete = graph.tasks[-2]
    assert task_to_delete.task_id == "7"
    os.remove(executor._task_cache._get_flag_filename(task_to_delete))

    task_results = list(executor.execute(graph))
    assert len(task_results) == 9
    for task, result in task_results:
        if task.task_id == "final":
            assert result == [0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7]


def test_get_active_tasks_when_partial_computation(executor, tmpdir):
    graph = _create_graph_with_result_passing()

    # initial execution of the graph
    executor._task_cache = FileTaskCache(work_dir=tmpdir)
    assert len(executor.get_active_tasks()) == 0
    for _ in executor.execute(graph):
        executor.get_active_tasks()
    assert len(executor.get_active_tasks()) == 0

    # now force partial recomputation
    executor._task_cache = FileTaskCache(work_dir=tmpdir)
    task_to_delete = graph.tasks[-2]
    assert task_to_delete.task_id == "7"
    os.remove(executor._task_cache._get_flag_filename(task_to_delete))

    assert len(executor.get_active_tasks()) == 0
    for _ in executor.execute(graph):
        executor.get_active_tasks()
    assert len(executor.get_active_tasks()) == 0


def _create_graph_with_result_passing():
    def add_to_list(what, where):
        return where + [what]

    def concat_lists(*lists):
        res = []
        for next_list in lists:
            res.extend(next_list)
        return res

    # create the task graph
    graph = TaskGraph()
    first_task = graph.create_task("0", add_to_list, [0, []], [])
    add_tasks = []
    for i in range(1, 8):
        add_tasks.append(
            graph.create_task(f"{i}", add_to_list, [i, first_task], [])
        )
    graph.create_task("final", concat_lists, add_tasks, [])
    return graph
