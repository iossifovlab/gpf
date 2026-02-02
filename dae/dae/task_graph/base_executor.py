from __future__ import annotations

import logging
import multiprocessing as mp
import os
import pickle  # noqa: S403
import time
from abc import abstractmethod
from collections.abc import Iterator
from copy import copy
from typing import Any

import fsspec
import psutil

from dae.task_graph.cache import CacheRecordType, NoTaskCache, TaskCache
from dae.task_graph.executor import TaskGraphExecutor
from dae.task_graph.graph import Task, TaskDesc, TaskGraph
from dae.task_graph.logging import (
    configure_task_logging,
    ensure_log_dir,
    safe_task_id,
)

logger = logging.getLogger(__name__)

NO_TASK_CACHE = NoTaskCache()


class TaskGraphExecutorBase(TaskGraphExecutor):
    """Executor that walks the graph in order that satisfies dependancies."""

    def __init__(self, task_cache: TaskCache = NO_TASK_CACHE, **kwargs: Any):
        super().__init__()
        self._task_cache = task_cache
        self._executing = False

        log_dir = ensure_log_dir(**kwargs)
        self._params = copy(kwargs)
        self._params["task_log_dir"] = log_dir

    @staticmethod
    def _exec_internal(
        task: TaskDesc,
        params: dict[str, Any],
    ) -> Any:
        verbose = params.get("verbose")
        if verbose is None:  # Dont use .get default in case of a Box
            verbose = 0

        log_dir = params.get("task_log_dir", ".")
        task_id = safe_task_id(task.task.task_id)
        task_func = task.func
        args = task.args

        root_logger = logging.getLogger()
        handler = configure_task_logging(log_dir, task_id, verbose)
        root_logger.addHandler(handler)

        task_logger = logging.getLogger("task_executor")
        task_logger.info("task <%s> started", task_id)

        start = time.time()

        process = psutil.Process(os.getpid())
        start_memory_mb = process.memory_info().rss / (1024 * 1024)
        task_logger.info(
            "worker process memory usage: %.2f MB", start_memory_mb)

        try:
            result = task_func(*args)
        except Exception as exp:  # noqa: BLE001
            # pylint: disable=broad-except
            result = exp

        elapsed = time.time() - start
        task_logger.info("task <%s> finished in %0.2fsec", task_id, elapsed)

        finish_memory_mb = process.memory_info().rss / (1024 * 1024)
        task_logger.info(
            "worker process memory usage: %.2f MB; change: %+0.2f MB",
            finish_memory_mb, finish_memory_mb - start_memory_mb)

        root_logger.removeHandler(handler)
        handler.close()
        return result

    @staticmethod
    def _exec_forked(
        task: TaskDesc,
        params: dict[str, Any],
    ) -> None:
        task_id = safe_task_id(task.task.task_id)
        result_fn = TaskGraphExecutorBase._result_fn(task_id, params)
        result = TaskGraphExecutorBase._exec_internal(task, params)

        try:
            with fsspec.open(result_fn, "wb") as out:
                pickle.dump(result, out)  # pyright: ignore
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "cannot write result for task %s. Ignoring and continuing.",
                result_fn,
            )

    @staticmethod
    def _result_fn(task_id: str, params: dict[str, Any]) -> str:
        status_dir = params.get("task_status_dir", ".")
        return os.path.join(status_dir, f"{task_id}.result")

    @staticmethod
    def _exec(
        task: TaskDesc,
        params: dict[str, Any],
    ) -> Any:
        fork_tasks = params.get("fork_tasks", False)
        if not fork_tasks:
            return TaskGraphExecutorBase._exec_internal(task, params)
        mp.current_process()._config[  # type: ignore  # noqa: SLF001
            "daemon"] = False
        p = mp.Process(
            target=TaskGraphExecutorBase._exec_forked,
            args=(task, params),
        )
        p.start()
        p.join()

        task_id = safe_task_id(task.task.task_id)
        result_fn = TaskGraphExecutorBase._result_fn(task_id, params)
        try:
            with fsspec.open(result_fn, "rb") as infile:
                result = pickle.load(infile)  # pyright: ignore
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "cannot write result for task %s. Ignoring and continuing.",
                result_fn,
            )
            result = None
        return result

    def execute(self, graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        assert not self._executing, \
            "Cannot execute a new graph while an old one is still running."

        self._executing = True

        completed_tasks: dict[Task, Any] = {}
        for task, record in self._task_cache.load(graph):
            if record.type == CacheRecordType.COMPUTED:
                result = record.result
                completed_tasks[task] = result

        graph.process_completed_tasks(list(completed_tasks.items()))

        for task, result in completed_tasks.items():
            yield task, result

        for task_node, result in self._execute(graph):
            is_error = isinstance(result, BaseException)
            self._task_cache.cache(
                task_node,
                is_error=is_error,
                result=result,
            )
            yield task_node, result

        self._executing = False

    @abstractmethod
    def _execute(self, graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        """Execute the given task graph.

        Args:
            task_graph: Task graph to execute.

        Yields:
            Tuples of (task, result) as tasks complete.
        """
