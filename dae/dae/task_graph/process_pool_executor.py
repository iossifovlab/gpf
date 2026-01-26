from __future__ import annotations

import logging
import os
import time
from collections import deque
from collections.abc import Callable, Iterator
from concurrent.futures import (
    Future,
    ProcessPoolExecutor,
    as_completed,
)
from copy import copy
from typing import Any

import psutil

from dae.task_graph.base_executor import TaskGraphExecutorBase
from dae.task_graph.graph import Task, TaskDesc, TaskGraph
from dae.task_graph.logging import (
    safe_task_id,
)

logger = logging.getLogger(__name__)


class ProcessPoolTaskExecutor(TaskGraphExecutorBase):
    """Execute tasks in parallel using Dask to do the heavy lifting."""

    def __init__(
        self, **kwargs: Any,
    ):
        super().__init__(**kwargs)
        max_workers = kwargs.get("n_threads", os.cpu_count() or 1)
        self._executor = ProcessPoolExecutor(max_workers=max_workers)

    def _submit_task(self, task: TaskDesc) -> Future:
        assert len(task.deps) == 0
        assert not any(isinstance(arg, Task) for arg in task.args), \
            "Task has no dependencies to wait for."

        params = copy(self._params)
        task_id = safe_task_id(task.task.task_id)
        params["task_id"] = task_id

        future = self._executor.submit(
            self._exec_internal, task.func, task.args, params,
        )
        if future is None:
            raise ValueError(
                f"unexpected dask executor return None: {task}, {task.args}, "
                f"{params}")
        assert future is not None

        return future

    @staticmethod
    def _exec_internal(
        task_func: Callable, args: list, params: dict[str, Any],
    ) -> Any:
        start = time.time()
        process = psutil.Process(os.getpid())
        start_memory_mb = process.memory_info().rss / (1024 * 1024)
        task_id = params["task_id"]

        logger.info(
            "worker process memory usage: %.2f MB", start_memory_mb)

        result = task_func(*args)
        elapsed = time.time() - start
        logger.info("task <%s> finished in %0.2fsec", task_id, elapsed)

        finish_memory_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(
            "worker process memory usage: %.2f MB; change: %+0.2f MB",
            finish_memory_mb, finish_memory_mb - start_memory_mb)

        return result

    def _schedule_tasks(
        self, graph: TaskGraph,
    ) -> dict[Future, Task]:
        ready_tasks = graph.extract_tasks(graph.ready_tasks())
        submitted_tasks: dict[Future, Task] = {}
        if ready_tasks:
            logger.debug("scheduling %d tasks", len(ready_tasks))
            for task in ready_tasks:
                future = self._submit_task(task)
                submitted_tasks[future] = task.task

        return submitted_tasks

    def _execute(self, graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        not_completed: set[Future] = set()
        completed: deque[Future] = deque()
        initial_task_count = len(graph)
        finished_tasks = 0
        process = psutil.Process(os.getpid())
        current_memory_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(
            "executor memory usage: %.2f MB", current_memory_mb)
        submitted_tasks: dict[Future, Task] = {}

        while not_completed or not graph.empty():
            submitted_tasks.update(self._schedule_tasks(graph))

            not_completed.update(submitted_tasks.keys())

            try:
                for future in as_completed(not_completed, timeout=0.25):
                    not_completed.remove(future)
                    completed.append(future)
            except TimeoutError:
                pass

            processed: list[tuple[Task, Any]] = []
            logger.debug("going to process %d completed tasks", len(completed))
            while completed:
                future = completed.popleft()
                task = submitted_tasks[future]
                try:
                    result = future.result()
                except Exception as ex:  # noqa: BLE001
                    # pylint: disable=broad-except
                    result = ex

                graph.process_completed_tasks([(task, result)])

                finished_tasks += 1
                processed.append((task, result))
                logger.info(
                    "finished %s/%s", finished_tasks,
                    initial_task_count)
                # del ref to future in order to make dask gc its resources
                del submitted_tasks[future]

            logger.debug("processed %d completed tasks", len(processed))
            yield from processed

        # clean up
        assert len(submitted_tasks) == 0, \
            "[BUG] Dask Executor's future queue is not empty."
        assert len(graph) == 0

    def close(self) -> None:
        self._executor.shutdown()
