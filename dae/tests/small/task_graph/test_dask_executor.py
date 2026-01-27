# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
from collections.abc import Generator

import pytest
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
    if request.param == "sequential":
        return SequentialExecutor()
    if request.param == "process_pool":
        return ProcessPoolTaskExecutor()
    raise ValueError(f"unknown executor type: {request.param}")


def noop() -> None:
    pass


@pytest.mark.parametrize(
    "tasks,expected_order", [
        (  # 0: simple chain
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["B"]),
            ],
            [["A"], ["B"], ["C"]],
        ),
        (  # 1: diamond
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B", "C"]),
            ],
            [["A"], ["B", "C"], ["D"]],
        ),
        (  # 2: wide graph
            [
                ("A", []),
                ("B", []),
                ("C", []),
                ("D", []),
                ("E", ["A", "B", "C", "D"]),
            ],
            [["A", "B", "C", "D"], ["E"]],
        ),
        (  # 3: complex graph
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["B", "C"]),
                ("F", ["D", "E"]),
            ],
            [["A"], ["B", "C"], ["D", "E"], ["F"]],
        ),
        (
            [  # 4: multiple roots
                ("A", []),
                ("B", []),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["C", "D"]),
            ],
            [["A", "B", "C", "D"], ["E"]],
        ),
        (
            [  # 5: multiple independent chains
                ("A1", []),
                ("B1", ["A1"]),
                ("C1", ["B1"]),
                ("A2", []),
                ("B2", ["A2"]),
                ("C2", ["B2"]),
            ],
            [["A1", "A2", "B1", "B2", "C1", "C2"]],
        ),
        (
            [  # 6: simple graph with numeric ids
                ("3", []),
                ("2", []),
                ("1", ["2", "3"]),
            ],
            [["2", "3"], ["1"]],
        ),
    ],
)
def test_dask_executor(
    executor: TaskGraphExecutor,
    tasks: list[tuple[str, list[str]]],
    expected_order: list[list[str]],
) -> None:
    graph = TaskGraph()
    for task_id, dep_ids in tasks:
        deps = [Task(dep_id) for dep_id in dep_ids]
        graph.create_task(task_id, noop, args=[], deps=deps)

    executed_tasks = list(executor.execute(graph))
    executed_task_ids: list[str] = [
        task.task_id for task, _ in executed_tasks]
    index = 0
    for expected_group in expected_order:
        executed_group = set()
        for _ in expected_group:
            executed_group.add(executed_task_ids[index])
            index += 1
        assert set(expected_group) == executed_group
