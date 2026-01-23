from collections.abc import Callable, Iterator
from typing import Any

from dask.distributed import Client, Future, as_completed

from dae.task_graph.cache import NoTaskCache, TaskCache
from dae.task_graph.executor import TaskGraphExecutor
from dae.task_graph.graph import Task, TaskGraph, TaskGraph2

NO_TASK_CACHE = NoTaskCache()


class DaskExecutor2(TaskGraphExecutor):
    """Dask-based task graph executor."""

    def __init__(
        self, dask_client: Client,
        task_cache: TaskCache = NO_TASK_CACHE, **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Initialize the Dask executor.

        Args:
            dask_client: Dask client to use for task execution.
        """
        super().__init__()
        self._dask_client = dask_client

    @staticmethod
    def _exec_internal(
        task_func: Callable, args: list, _deps: list, params: dict[str, Any],
    ) -> Any:
        verbose = params.get("verbose")
        if verbose is None:  # Dont use .get default in case of a Box
            verbose = 0

        return task_func(*args)

    def execute(self, task_graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        """Execute the given task graph using Dask.

        Args:
            task_graph: Task graph to execute.

        Yields:
            Tuples of (task, result) as tasks complete.
        """

        graph = TaskGraph2.from_task_graph(task_graph)
        yield from self.execute2(graph)

    def execute2(
        self, graph: TaskGraph2,
    ) -> Iterator[tuple[Task, Any]]:
        """Execute the given task graph using Dask.

        Args:
            task_graph: Task graph to execute.

        Yields:
            Tuples of (task, result) as tasks complete.
        """
        while not graph.empty():
            futures: dict[Future, Task] = {}
            for task in graph.ready_tasks():
                future = self._dask_client.submit(
                    self._exec_internal, task.func, task.args, [], {},
                    key=task.task_id,
                    pure=False,
                )
                futures[future] = task

            for future in as_completed(futures):
                result = future.result()
                task = futures[future]
                graph.process_completed_tasks([(task.task_id, result)])
                yield task, result

    def close(self) -> None:
        """Close the Dask executor."""
        self._dask_client.close()
