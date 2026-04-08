# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
from collections.abc import Generator

import pytest
from dask.distributed import Client
from gain.task_graph.dask_executor import DaskExecutor
from gain.task_graph.executor import (
    TaskGraphExecutor,
)
from gain.task_graph.process_pool_executor import ProcessPoolTaskExecutor
from gain.task_graph.sequential_executor import SequentialExecutor


@pytest.fixture
def dask_client() -> Generator[Client, None, None]:
    # The client needs to be threaded b/c the global ORDER variable is modified
    client = Client(n_workers=2, threads_per_worker=1, processes=False)
    yield client
    client.close()


@pytest.fixture(params=["dask", "sequential", "process_pool"])  # "process_pool"
def executor(
    dask_client: Client,
    request: pytest.FixtureRequest,
) -> Generator[TaskGraphExecutor, None, None]:
    executor: TaskGraphExecutor

    if request.param == "dask":
        executor = DaskExecutor(dask_client)
    elif request.param == "sequential":
        executor = SequentialExecutor()
    elif request.param == "process_pool":
        if not request.config.getoption("enable_pp"):
            pytest.skip("process_pool executor not enabled")
        executor = ProcessPoolTaskExecutor()
    else:
        raise ValueError(f"unknown executor type: {request.param}")

    yield executor
    executor.close()
