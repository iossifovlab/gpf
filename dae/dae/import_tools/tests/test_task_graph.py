# pylint: disable=W0621,C0114,C0116,W0212,W0613
import time
import pytest

from dask.distributed import Client  # type: ignore

from dae.import_tools.task_graph import DaskExecutor, SequentialExecutor,\
    TaskGraph


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


# NOTE these tests should not run in parallel
EXEC_ORDER = []


def do_work(name, timeout):
    if timeout != 0:
        time.sleep(timeout)
    EXEC_ORDER.append(name)


def test_dependancy_chain(executor):
    global EXEC_ORDER  # pylint: disable=global-statement
    EXEC_ORDER = []
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", do_work, ["task_1", 0.01], [])
    graph.create_task("Task 1", do_work, ["task_2", 0], [task_1])

    executor.execute(graph)

    assert EXEC_ORDER == ["task_1", "task_2"]


def test_multiple_dependancies(executor):
    global EXEC_ORDER  # pylint: disable=global-statement
    EXEC_ORDER = []
    graph = TaskGraph()

    tasks = []
    for i in range(10):
        task = graph.create_task(f"Task {i}", do_work, [f"task_{i}", 0], [])
        tasks.append(task)

    for i in range(100, 105):
        graph.create_task(f"Task {i}", do_work, [f"task_{i}", 0], tasks)

    executor.execute(graph)

    assert len(EXEC_ORDER) == 15
    assert set(EXEC_ORDER[:10]) == set(f"task_{i}" for i in range(10))
    assert set(EXEC_ORDER[10:]) == set(f"task_{i}" for i in range(100, 105))


def assign_to_execution_order(list_obj):
    EXEC_ORDER.extend(list_obj)


def test_implicit_dependancies(executor):
    global EXEC_ORDER  # pylint: disable=global-statement
    EXEC_ORDER = []
    graph = TaskGraph()

    def add_to_list(what, where):
        where.append(what)
        return where

    last_task = graph.create_task("0", add_to_list, [0, []], [])
    for i in range(1, 8):
        last_task = graph.create_task(f"{i}", add_to_list, [i, last_task], [])

    graph.create_task("8", assign_to_execution_order, [last_task], [])

    executor.execute(graph)

    assert EXEC_ORDER == list(range(8))
