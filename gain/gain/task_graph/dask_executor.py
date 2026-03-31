import logging
import threading
import time
from collections.abc import Iterator
from copy import copy
from typing import Any

from dask.distributed import Client, Future, wait

from gain.task_graph.base_executor import TaskGraphExecutorBase
from gain.task_graph.cache import NoTaskCache, TaskCache
from gain.task_graph.graph import Task, TaskDesc, TaskGraph
from gain.task_graph.logging import (
    ensure_log_dir,
    safe_task_id,
)

NO_TASK_CACHE = NoTaskCache()
logger = logging.getLogger(__name__)


class DaskExecutor(TaskGraphExecutorBase):
    """Dask-based task graph executor."""

    def __init__(
        self, dask_client: Client,
        task_cache: TaskCache = NO_TASK_CACHE, **kwargs: Any,
    ) -> None:
        """Initialize the Dask executor.

        Args:
            dask_client: Dask client to use for task execution.
        """
        super().__init__(task_cache=task_cache, **kwargs)
        self._executing = False
        self._dask_client = dask_client

        log_dir = ensure_log_dir(**kwargs)
        self._params = copy(kwargs)
        self._params["task_log_dir"] = log_dir

    def _submit_worker_func(
        self,
        submit_queue: list[TaskDesc | None],
        submit_condition: threading.Condition,
        running: dict[Future, Task],
        running_lock: threading.Lock,
    ) -> None:
        start = time.time()
        submit_count = 0

        while True:
            tasks: list[TaskDesc | None] = []

            with submit_condition:
                if not submit_queue:
                    submit_condition.wait()
                tasks = copy(submit_queue)
                submit_queue.clear()

            if any(t is None for t in tasks):
                logger.warning(
                    "submit worker received shutdown signal; "
                    "skipping %s tasks...",
                    len(tasks) - 1)
                return

            assert all(isinstance(t, TaskDesc) for t in tasks)
            task_ids = [
                safe_task_id(task.task.task_id)
                for task in tasks
                if task is not None
            ]

            futures = self._dask_client.map(
                            self._exec, tasks,
                            key=task_ids,
                            pure=False,
                            params=self._params,
                        )

            with running_lock:
                for future, task in zip(futures, tasks, strict=True):
                    assert task is not None
                    submit_count += 1
                    running[future] = task.task
                    total_running = len(running)
            elapsed = time.time() - start
            logger.debug(
                "submitted %s tasks in %.2f seconds; %.2f tasks/s",
                submit_count, elapsed, submit_count / elapsed)
            logger.debug(
                "total running tasks: %s", total_running)

    def _results_worker_func(
            self,
            completed_queue: list[tuple[Future, Task] | None],
            completed_condition: threading.Condition,
            results_queue: list[tuple[Task, Any]],
            results_lock: threading.Lock,
    ) -> None:
        shutdown_signal = False
        processed_results = 0

        with completed_condition:
            while True:
                if shutdown_signal and len(completed_queue) == 0:
                    break

                if completed_queue:
                    logger.debug(
                        "results worker processing %s completed tasks",
                        len(completed_queue))

                    if any(i is None for i in completed_queue):
                        logger.warning(
                            "results worker received shutdown signal; ")
                        shutdown_signal = True
                        completed_queue = [
                            i for i in completed_queue if i is not None]
                    if not completed_queue:
                        continue

                    futures, tasks = zip(*completed_queue, strict=True)
                    completed_queue.clear()

                    results = self._dask_client.gather(futures, errors="skip")

                    if len(results) == len(tasks):
                        with results_lock:
                            results_queue.extend(
                                zip(tasks, results, strict=True))
                        processed_results += len(results)
                        for future in futures:
                            future.release()

                    else:
                        logger.error(
                            "failed to gather results for all %s tasks; "
                            "looking for exceptions in futures...",
                            len(tasks))
                        for future, task in zip(futures, tasks, strict=True):
                            try:
                                result = future.result()
                            except Exception as ex:  # noqa: BLE001
                                # pylint: disable=broad-except
                                result = ex
                            with results_lock:
                                results_queue.append((task, result))
                            future.release()
                            processed_results += 1

                completed_condition.wait(timeout=0.05)

        logger.info("results worker processed %s results", processed_results)

    MAX_RUNNING_TASKS = 700

    def _execute(
        self, graph: TaskGraph,
    ) -> Iterator[tuple[Task, Any]]:
        self._executing = True

        submit_queue: list[TaskDesc | None] = []
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

        finished_tasks = 0
        initial_task_count = len(graph)

        while not is_done:
            with running_lock:
                total_running = len(running)
            if total_running < self.MAX_RUNNING_TASKS:
                limit = max(self.MAX_RUNNING_TASKS - total_running, 1)
                ready_tasks = graph.extract_tasks(
                    graph.ready_tasks(limit=limit))
                with submit_condition:
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
                    logger.debug(
                        "waited for completed tasks return %s futures",
                        len(completed))
                except TimeoutError:
                    completed = set()

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
                    graph.process_completed_tasks([(task, result)])
                    finished_tasks += 1
                    logger.info(
                        "finished %s/%s", finished_tasks,
                        initial_task_count)
                    yield task, result

            is_done = graph.empty()
            if is_done:
                for _ in range(3):
                    with submit_condition:
                        is_done = is_done and not submit_queue
                    with running_lock:
                        is_done = is_done and not running
                    with results_lock:
                        is_done = is_done and not results_queue
                    with completed_condition:
                        is_done = is_done and not completed_queue

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
        logger.info("closing Dask executor")
        self._dask_client.retire_workers(close_workers=True)
        self._dask_client.shutdown()
        self._dask_client.close()
        logger.info("Dask executor closed")
