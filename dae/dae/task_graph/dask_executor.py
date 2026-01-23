import logging
import threading
import time
from collections.abc import Callable, Iterator
from copy import copy
from typing import Any

from dask.distributed import Client, Future, wait

from dae.task_graph.cache import NoTaskCache, TaskCache
from dae.task_graph.executor import TaskGraphExecutor
from dae.task_graph.graph import Task, TaskGraph, TaskGraph2
from dae.task_graph.logging import (
    ensure_log_dir,
    safe_task_id,
)

NO_TASK_CACHE = NoTaskCache()
logger = logging.getLogger(__name__)


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
        self._executing = False
        self._dask_client = dask_client

        log_dir = ensure_log_dir(**kwargs)
        self._params = copy(kwargs)
        self._params["task_log_dir"] = log_dir

    def _submit_worker_func(
        self,
        submit_queue: list[Task | None],
        submit_condition: threading.Condition,
        running: dict[Future, Task],
        running_lock: threading.Lock,
    ) -> None:
        with submit_condition:
            while True:
                while submit_queue:
                    task = submit_queue.pop()
                    if task is None:
                        logger.warning(
                            "submit worker received shutdown signal.")
                        return
                    assert isinstance(task, Task)
                    params = copy(self._params)
                    task_id = safe_task_id(task.task_id)
                    params["task_id"] = task_id
                    logger.info("Submitting task %s to Dask", task_id)
                    future = self._dask_client.submit(
                        self._exec_internal, task.func, task.args, params,
                        key=task_id,
                    )
                    if future is None:
                        raise ValueError(
                            f"unexpected dask executor return None: "
                            f"{task}, {task.args}, "
                            f"{params}")
                    assert future is not None

                    with running_lock:
                        running[future] = task
                submit_condition.wait()

    def _results_worker_func(
            self,
            completed_queue: list[tuple[Future, Task] | None],
            completed_condition: threading.Condition,
            results_queue: list[tuple[Task, Any]],
            results_lock: threading.Lock,
    ) -> None:
        with completed_condition:
            while True:
                logger.warning("Waiting for completed task...")
                while completed_queue:
                    item = completed_queue.pop()
                    if item is None:
                        logger.warning(
                            "Results worker received shutdown signal.")
                        return
                    future, task = item
                    logger.info("Processing completed task %s", task.task_id)

                    try:
                        result = future.result()
                    except Exception as ex:  # noqa: BLE001
                        # pylint: disable=broad-except
                        result = ex

                    with results_lock:
                        results_queue.append((task, result))
                completed_condition.wait()

    @staticmethod
    def _exec_internal(
        task_func: Callable, args: list, params: dict[str, Any],
    ) -> Any:
        try:
            logger.warning("Executing task %s", params["task_id"])
            logger.info("task %s started with args %s", params["task_id"], args)
            result = task_func(*args)
            logger.info("task %s finished", params["task_id"])

        except Exception:
            logger.exception(
                "task %s failed with exception", params["task_id"])
            raise

        return result

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
        assert not self._executing, \
            "Cannot execute a new graph while an old one is still running."
        self._executing = True

        submit_queue: list[Task | None] = []
        submit_condition: threading.Condition = threading.Condition()

        running_lock: threading.Lock = threading.Lock()
        running: dict[Future, Task] = {}

        completed_queue: list[tuple[Future, Task] | None] = []
        completed_condition: threading.Condition = threading.Condition()

        results_queue: list[tuple[Task, Any]] = []
        results_lock: threading.Lock = threading.Lock()

        submit_worker = threading.Thread(
            target=self._submit_worker_func,
            args=(
                submit_queue, submit_condition,
                running, running_lock),
            daemon=True)
        submit_worker.start()

        results_worker = threading.Thread(
            target=self._results_worker_func,
            args=(
                completed_queue, completed_condition,
                results_queue, results_lock),
            daemon=True)
        results_worker.start()

        not_completed: set[Future] = set()
        is_done: bool = graph.empty()

        while not is_done:
            with submit_condition:
                ready_tasks = list(graph.ready_tasks())
                if ready_tasks:
                    submit_queue.extend(ready_tasks)
                    submit_condition.notify_all()

            with running_lock:
                not_completed = set(running.keys())

            if not not_completed:
                time.sleep(0.05)
                completed = set()
            else:
                try:
                    completed, not_completed = wait(
                        not_completed,
                        return_when="FIRST_COMPLETED",
                        timeout=0.05,
                    )
                except TimeoutError:
                    completed = set()

            logger.info(
                "DaskExecutor2: %d running, %d completed tasks",
                len(running),
                len(completed),
            )
            with running_lock, completed_condition:
                for future in completed:
                    task = running[future]
                    del running[future]
                    completed_queue.append((future, task))
                completed_condition.notify_all()

            with results_lock:
                while results_queue:
                    item = results_queue.pop(0)
                    task, result = item
                    graph.process_completed_tasks([(task.task_id, result)])
                    yield task, result
            with results_lock, submit_condition, \
                    completed_condition, submit_condition:
                is_done = (
                    graph.empty()
                    and not submit_queue
                    and not running
                    and not completed_queue
                    and not results_queue
                )

        with submit_condition:
            submit_queue.append(None)
            submit_condition.notify_all()

        with completed_condition:
            completed_queue.append(None)
            completed_condition.notify_all()

        results_worker.join()
        submit_worker.join()
        self._executing = False

    def close(self) -> None:
        """Close the Dask executor."""
        self._dask_client.close()
