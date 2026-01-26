from __future__ import annotations

import logging
import multiprocessing as mp
import os
import pickle  # noqa: S403
import time
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Generator, Iterator, Sequence
from copy import copy
from types import TracebackType
from typing import Any

import fsspec
import networkx
import psutil

from dae.task_graph.cache import CacheRecordType, NoTaskCache, TaskCache
from dae.task_graph.graph import Task, TaskGraph, TaskGraph2
from dae.task_graph.logging import (
    configure_task_logging,
    ensure_log_dir,
)

logger = logging.getLogger(__name__)


class TaskGraphExecutor:
    """Class that executes a task graph."""

    @abstractmethod
    def execute(self, task_graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        """Start executing the graph.

        Return an iterator that yields the task in the graph
        after they are executed.

        This is not nessessarily in DFS or BFS order.
        This is not even the order in which these tasks are executed.

        The only garantee is that when a task is returned its executions
        is already finished.
        """

    @abstractmethod
    def execute2(self, task_graph: TaskGraph2) -> Iterator[tuple[Task, Any]]:
        """Start executing the graph.

        Return an iterator that yields the task in the graph
        after they are executed.

        This is not nessessarily in DFS or BFS order.
        This is not even the order in which these tasks are executed.

        The only garantee is that when a task is returned its executions
        is already finished.
        """

    def __enter__(self) -> TaskGraphExecutor:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.close()
        return exc_type is None

    @abstractmethod
    def close(self) -> None:
        """Clean-up any resources used by the executor."""


NO_TASK_CACHE = NoTaskCache()


class AbstractTaskGraphExecutor(TaskGraphExecutor):
    """Executor that walks the graph in order that satisfies dependancies."""

    def __init__(self, task_cache: TaskCache = NO_TASK_CACHE, **kwargs: Any):
        super().__init__()
        self._task_cache = task_cache
        self._executing = False
        self._task_queue: dict[str, Task] = {}
        self._task_dependants: dict[str, set[str]] = defaultdict(set)

        log_dir = ensure_log_dir(**kwargs)
        self._params = copy(kwargs)
        self._params["task_log_dir"] = log_dir

    def _queue_size(self) -> int:
        return 1

    @staticmethod
    def _ready_to_run(task: Task) -> bool:
        return not task.deps

    def _select_tasks_to_run(
        self, limit: int,
    ) -> list[Task]:
        started = time.time()
        selected_tasks: list[Task] = []
        di_graph = AbstractTaskGraphExecutor._build_di_graph(self._task_queue)

        for task_id in networkx.topological_sort(di_graph):
            if task_id not in self._task_queue:
                break
            task = self._task_queue[task_id]
            elapsed = time.time() - started
            if elapsed > 1.0:
                logger.debug(
                    "selecting tasks to run took too long (%.2f sec), "
                    "stopping search", elapsed)
                break
            if not self._ready_to_run(task):
                break
            selected_tasks.append(task)
            if len(selected_tasks) >= limit:
                break
        elapsed = time.time() - started
        logger.debug(
            "selecting %s tasks to run took %.2f sec",
            len(selected_tasks), elapsed)
        del di_graph
        return selected_tasks

    def _prune_dependants(self, task_id: str) -> None:
        started = time.time()
        dependents = self._task_dependants.get(task_id, set())
        for dep_id in dependents:
            logger.debug("pruning dependent task %s", dep_id)
            if dep_id not in self._task_queue:
                continue
            del self._task_queue[dep_id]
        elapsed = time.time() - started
        logger.debug(
            "pruning dependents of task %s took %.2f sec", task_id, elapsed)

    @staticmethod
    def _exec_internal(
        task_func: Callable, args: list, _deps: list, params: dict[str, Any],
    ) -> Any:
        verbose = params.get("verbose")
        if verbose is None:  # Dont use .get default in case of a Box
            verbose = 0

        task_id = params["task_id"]
        log_dir = params.get("task_log_dir", ".")

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

        result = task_func(*args)
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
        task_func: Callable, args: list, deps: list, params: dict[str, Any],
    ) -> None:

        result_fn = AbstractTaskGraphExecutor._result_fn(params)
        try:
            result = AbstractTaskGraphExecutor._exec_internal(
                task_func, args, deps, params,
            )
        except Exception as exp:  # noqa: BLE001
            # pylint: disable=broad-except
            result = exp
        try:
            with fsspec.open(result_fn, "wb") as out:
                pickle.dump(result, out)  # pyright: ignore
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "cannot write result for task %s. Ignoring and continuing.",
                result_fn,
            )

    @staticmethod
    def _result_fn(params: dict[str, Any]) -> str:
        task_id = params["task_id"]
        status_dir = params.get("task_status_dir", ".")
        return os.path.join(status_dir, f"{task_id}.result")

    @staticmethod
    def _exec(
        task_func: Callable, args: list, _deps: list, params: dict[str, Any],
    ) -> Any:
        fork_tasks = params.get("fork_tasks", False)
        if not fork_tasks:
            return AbstractTaskGraphExecutor._exec_internal(
                task_func, args, _deps, params,
            )
        mp.current_process()._config[  # type: ignore  # noqa: SLF001
            "daemon"] = False
        p = mp.Process(
            target=AbstractTaskGraphExecutor._exec_forked,
            args=(task_func, args, _deps, params),
        )
        p.start()
        p.join()

        result_fn = AbstractTaskGraphExecutor._result_fn(params)
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

    def execute(self, task_graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        assert not self._executing, \
            "Cannot execute a new graph while an old one is still running."
        self._check_for_cyclic_deps(task_graph)
        self._executing = True
        completed_tasks: dict[Task, Any] = {}

        for task in self._in_exec_order(task_graph):
            self._queue_task(task)

        for task, record in self._task_cache.load(task_graph):
            if record.type == CacheRecordType.COMPUTED:
                result = record.result
                completed_tasks[task] = result
                task_dependants = self._task_dependants.get(task.task_id, set())
                for dep_id in task_dependants:
                    if dep_id not in self._task_queue:
                        continue
                    dep_task = self._task_queue[dep_id]
                    dep_task = self._reconfigure_task_node_deps(
                        dep_task, task, result)
                    self._task_queue[dep_id] = dep_task
                del self._task_queue[task.task_id]

        return self._yield_task_results(completed_tasks)

    def _yield_task_results(
        self, already_computed_tasks: dict[Task, Any],
    ) -> Iterator[tuple[Task, Any]]:
        for task_node, result in already_computed_tasks.items():
            yield task_node, result
        for task_node, result in self._await_tasks():
            is_error = isinstance(result, BaseException)
            self._task_cache.cache(
                task_node,
                is_error=is_error,
                result=result,
            )
            yield task_node, result
        self._executing = False

    def _collect_deps(
        self, task_node: Task,
        result: set[str] | None = None,
    ) -> set[str]:
        if result is None:
            result = set()

        for dep in task_node.deps:
            result.add(dep.task_id)
            self._collect_deps(dep, result)
        return result

    def _queue_task(self, task_node: Task) -> None:
        self._task_queue[task_node.task_id] = task_node
        for dep_id in self._collect_deps(task_node):
            self._task_dependants[dep_id].add(task_node.task_id)

    @abstractmethod
    def _await_tasks(self) -> Iterator[tuple[Task, Any]]:
        """Yield enqueued tasks as soon as they finish."""

    @staticmethod
    def _in_exec_order(
        task_graph: TaskGraph,
    ) -> Sequence[Task]:
        return list(AbstractTaskGraphExecutor._toplogical_order(task_graph))

    @staticmethod
    def _build_di_graph(
        tasks: dict[str, Task],
    ) -> networkx.DiGraph:

        di_graph = networkx.DiGraph()
        nodes: list[str] = list(tasks.keys())
        di_graph.add_nodes_from(sorted(nodes))

        for task in tasks.values():
            for dep in task.deps:
                di_graph.add_edge(dep.task_id, task.task_id)
        return di_graph

    @staticmethod
    def _toplogical_order(
        task_graph: TaskGraph,
    ) -> Generator[Task, None, None]:
        queue: dict[str, Task] = {}
        for task in task_graph.tasks:
            if task.task_id not in queue:
                queue[task.task_id] = task

        graph = AbstractTaskGraphExecutor._build_di_graph(queue)

        for task_id in networkx.topological_sort(graph):
            task = queue.pop(task_id)
            yield task

    @staticmethod
    def _check_for_cyclic_deps(task_graph: TaskGraph) -> None:
        visited: set[Task] = set()
        stack: list[Task] = []
        for node in task_graph.tasks:
            if node not in visited:
                cycle = AbstractTaskGraphExecutor._find_cycle(
                    node, visited, stack)
                if cycle is not None:
                    raise ValueError(f"Cyclic dependency {cycle}")

    @staticmethod
    def _find_cycle(
        node: Task, visited: set[Task], stack: list[Task],
    ) -> list[Task] | None:
        visited.add(node)
        stack.append(node)

        for dep in node.deps:
            if dep not in visited:
                return AbstractTaskGraphExecutor._find_cycle(
                    dep, visited, stack)
            if dep in stack:
                return copy(stack)

        stack.pop()
        return None

    def close(self) -> None:
        pass

    def _reconfigure_task_node_deps(
        self, task: Task, completed_task: Task, completed_result: Any,
    ) -> Task:
        args = []
        for arg in task.args:
            if isinstance(arg, Task) and arg.task_id == completed_task.task_id:
                arg = completed_result
            args.append(arg)

        deps = []
        for dep in task.deps:
            if dep.task_id == completed_task.task_id:
                continue
            deps.append(dep)

        return Task(
            task.task_id,
            task.func,
            args,
            deps,
            task.input_files,
        )

    def _process_completed_task(
        self, task: Task, result: Any,
    ) -> None:
        if isinstance(result, BaseException):
            self._prune_dependants(task.task_id)
            return
        task_dependants = self._task_dependants.get(task.task_id, set())
        for dep_id in task_dependants:
            if dep_id not in self._task_queue:
                continue
            dep_task = self._task_queue[dep_id]
            dep_task = self._reconfigure_task_node_deps(dep_task, task, result)
            self._task_queue[dep_id] = dep_task

        if task.task_id in self._task_dependants:
            del self._task_dependants[task.task_id]
