# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
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


class Worker:
    # NOTE these tests should not run in parallel
    EXEC_ORDER: list[str] = []

    @classmethod
    def do_work(cls, name, timeout):
        if timeout != 0:
            time.sleep(timeout)
        cls.EXEC_ORDER.append(name)

    @classmethod
    def assign_to_execution_order(cls, list_obj):
        cls.EXEC_ORDER.extend(list_obj)


@pytest.fixture
def worker():
    Worker.EXEC_ORDER = []
    return Worker()


def test_dependancy_chain(executor, worker):
    graph = TaskGraph()
    task_1 = graph.create_task("Task 1", worker.do_work, ["task_1", 0.01], [])
    graph.create_task("Task 1", worker.do_work, ["task_2", 0], [task_1])

    executor.execute(graph)

    assert worker.EXEC_ORDER == ["task_1", "task_2"]


def test_multiple_dependancies(executor, worker):
    graph = TaskGraph()

    tasks = []
    for i in range(10):
        task = graph.create_task(
            f"Task {i}", worker.do_work, [f"task_{i}", 0], []
        )
        tasks.append(task)

    for i in range(100, 105):
        graph.create_task(f"Task {i}", worker.do_work, [f"task_{i}", 0], tasks)

    executor.execute(graph)

    assert len(worker.EXEC_ORDER) == 15
    assert set(worker.EXEC_ORDER[:10]) == set(f"task_{i}" for i in range(10))
    assert set(worker.EXEC_ORDER[10:]) == set(
        f"task_{i}" for i in range(100, 105)
    )


def test_implicit_dependancies(executor, worker):
    graph = TaskGraph()

    def add_to_list(what, where):
        where.append(what)
        return where

    last_task = graph.create_task("0", add_to_list, [0, []], [])
    for i in range(1, 8):
        last_task = graph.create_task(f"{i}", add_to_list, [i, last_task], [])

    graph.create_task("8", worker.assign_to_execution_order, [last_task], [])

    executor.execute(graph)

    assert worker.EXEC_ORDER == list(range(8))
