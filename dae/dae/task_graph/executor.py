from __future__ import annotations

import logging
import sys
import time
import traceback
from abc import abstractmethod
from collections import deque
from collections.abc import Generator, Iterator
from copy import copy
from types import TracebackType
from typing import Any, Callable, Optional, cast

from dask.distributed import Client, Future

from dae.task_graph.cache import CacheRecordType, NoTaskCache, TaskCache
from dae.task_graph.graph import Task, TaskGraph
from dae.task_graph.logging import (
    configure_task_logging,
    ensure_log_dir,
    safe_task_id,
)
from dae.utils.verbosity_configuration import VerbosityConfiguration

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

    def __enter__(self) -> TaskGraphExecutor:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    @abstractmethod
    def close(self) -> None:
        """Clean-up any resources used by the executor."""


class AbstractTaskGraphExecutor(TaskGraphExecutor):
    """Executor that walks the graph in order that satisfies dependancies."""

    def __init__(self, task_cache: TaskCache = NoTaskCache()):
        super().__init__()
        self._task_cache = task_cache
        self._executing = False

    @staticmethod
    def _exec(
        task_func: Callable, args: list, _deps: list, params: dict[str, Any],
    ) -> Any:
        verbose = params.get("verbose")
        if verbose is None:  # Dont use .get default in case of a Box
            verbose = 0
        VerbosityConfiguration.set_verbosity(verbose)

        task_id = params["task_id"]
        log_dir = params.get("log_dir", ".")

        root_logger = logging.getLogger()
        handler = configure_task_logging(log_dir, task_id, verbose)
        root_logger.addHandler(handler)

        task_logger = logging.getLogger("task_executor")
        task_logger.info("task <%s> started", task_id)
        start = time.time()
        result = task_func(*args)
        elapsed = time.time() - start
        task_logger.info("task <%s> finished in %0.2fsec", task_id, elapsed)

        root_logger.removeHandler(handler)
        handler.close()
        return result

    def execute(self, task_graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        assert not self._executing, \
            "Cannot execute a new graph while an old one is still running."
        self._check_for_cyclic_deps(task_graph)
        self._executing = True

        already_computed_tasks = {}
        for task_node, record in self._task_cache.load(task_graph):
            if record.type == CacheRecordType.COMPUTED:
                already_computed_tasks[task_node] = record.result

        for task_node in self._in_exec_order(task_graph):
            if task_node in already_computed_tasks:
                task_result = already_computed_tasks[task_node]
                self._set_task_result(task_node, task_result)
            else:
                self._queue_task(task_node)
        return self._yield_task_results(already_computed_tasks)

    def _yield_task_results(
        self, already_computed_tasks: dict[Task, Any],
    ) -> Iterator[tuple[Task, Any]]:
        for task_node, result in already_computed_tasks.items():
            yield task_node, result
        for task_node, result in self._await_tasks():
            is_error = isinstance(result, BaseException)
            self._task_cache.cache(task_node, is_error, result)
            yield task_node, result
        self._executing = False

    @abstractmethod
    def _queue_task(self, task_node: Task) -> None:
        """Put the task on the execution queue."""

    @abstractmethod
    def _await_tasks(self) -> Iterator[tuple[Task, Any]]:
        """Yield enqueued tasks as soon as they finish."""

    @abstractmethod
    def _set_task_result(self, task: Task, result: Any) -> None:
        """Set a precomputed result for a task."""

    @staticmethod
    def _in_exec_order(
        task_graph: TaskGraph,
    ) -> Generator[Task, None, None]:
        visited: set[Task] = set()
        for node in task_graph.tasks:
            yield from AbstractTaskGraphExecutor._node_in_exec_order(
                node, visited)

    @staticmethod
    def _node_in_exec_order(
        node: Task, visited: set[Task],
    ) -> Generator[Task, None, None]:
        if node in visited:
            return
        visited.add(node)
        for dep in node.deps:
            yield from AbstractTaskGraphExecutor._node_in_exec_order(
                dep, visited)
        yield node

    @staticmethod
    def _check_for_cyclic_deps(task_graph: TaskGraph) -> None:
        visited: set[Task] = set()
        stack: list[Task] = []
        for node in task_graph.tasks:
            if node not in visited:
                cycle = AbstractTaskGraphExecutor._find_cycle(
                    node, visited, stack)
                if cycle is not None:
                    raise ValueError(f"Cyclic dependancy {cycle}")

    @staticmethod
    def _find_cycle(
        node: Task, visited: set[Task], stack: list[Task],
    ) -> Optional[list[Task]]:
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


class SequentialExecutor(AbstractTaskGraphExecutor):
    """A Task Graph Executor that executes task in sequential order."""

    def __init__(self, task_cache: TaskCache = NoTaskCache(), **kwargs: Any):
        super().__init__(task_cache)
        self._task_queue: list[Task] = []
        self._task2result: dict[Task, Any] = {}
        log_dir = ensure_log_dir(**kwargs)
        self._params = copy(kwargs)
        self._params["log_dir"] = log_dir

    def _queue_task(self, task_node: Task) -> None:
        self._task_queue.append(task_node)

    def _await_tasks(self) -> Generator[tuple[Task, Any], None, None]:
        finished_tasks = 0
        initial_task_count = len(self._task_queue)

        for task_node in self._task_queue:
            all_deps_satisfied = all(
                d in self._task2result for d in task_node.deps
            )
            if not all_deps_satisfied:
                # some of the dependancies were errors and didn't run
                logger.info(
                    "Skipping execution of task(id=%s) because one or more of "
                    "its dependancies failed with an error", task_node.task_id)
                continue

            # handle tasks that use the output of other tasks
            args = [
                self._task2result[arg] if isinstance(arg, Task) else arg
                for arg in task_node.args
            ]
            is_error = False

            params = copy(self._params)
            params["task_id"] = safe_task_id(task_node.task_id)

            try:
                result = self._exec(task_node.func, args, [], params)
            except Exception as exp:  # pylint: disable=broad-except
                result = exp
                is_error = True
            finished_tasks += 1
            logger.debug("clean up task %s", task_node)
            logger.info(
                "finished %s/%s", finished_tasks,
                initial_task_count)
            if not is_error:
                self._task2result[task_node] = result
            yield task_node, result

        # all tasks have already executed. Let's clean the state.
        self._task_queue = []
        self._task2result = {}

    def _set_task_result(self, task: Task, result: Any) -> None:
        self._task2result[task] = result


class DaskExecutor(AbstractTaskGraphExecutor):
    """Execute tasks in parallel using Dask to do the heavy lifting."""

    def __init__(
        self, client: Client, task_cache: TaskCache = NoTaskCache(),
        **kwargs: Any,
    ):
        super().__init__(task_cache)
        self._client = client
        self._task2future: dict[Task, Future] = {}
        self._future_key2task: dict[str, Task] = {}
        self._task2result: dict[Task, Any] = {}
        self._task_queue: deque[Task] = deque()
        log_dir = ensure_log_dir(**kwargs)
        self._params = copy(kwargs)
        self._params["log_dir"] = log_dir

    def _queue_task(self, task_node: Task) -> None:
        self._task_queue.append(task_node)

    def _submit_task(self, task_node: Task) -> Future:
        deps = []
        for dep in task_node.deps:
            future = self._task2future.get(dep)
            if future:
                deps.append(future)
            else:
                assert dep in self._task2result

        # handle tasks that use the output of other tasks
        args = []
        for arg in task_node.args:
            if isinstance(arg, Task):
                value = self._get_future_or_result(arg)
            else:
                value = arg
            args.append(value)
        params = copy(self._params)
        params["task_id"] = safe_task_id(task_node.task_id)

        future = self._client.submit(
            self._exec, task_node.func, args, deps, params, pure=False)
        if future is None:
            raise ValueError(
                f"unexpected dask executor return None: {task_node}, {args}, "
                f"{deps}, {params}")
        self._task2future[task_node] = future
        self._future_key2task[future.key] = task_node
        return future

    def _get_future_or_result(self, task: Task) -> Any:
        future = self._task2future.get(task)
        return future or self._task2result[task]

    MIN_QUEUE_SIZE = 700

    def _queue_size(self) -> int:
        n_workers = cast(int, sum(self._client.ncores().values()))
        return max(self.MIN_QUEUE_SIZE, 2 * n_workers)

    def _schedule_tasks(self, currently_running: set[Future]) -> set[Future]:
        while self._task_queue and len(currently_running) < self._queue_size():
            future = self._submit_task(self._task_queue.popleft())
            currently_running.add(future)
        return currently_running

    def _await_tasks(self) -> Generator[tuple[Task, Any], None, None]:
        # pylint: disable=import-outside-toplevel
        from dask.distributed import wait

        not_completed: set = set()
        completed = set()
        initial_task_count = len(self._task_queue)
        finished_tasks = 0

        not_completed = self._schedule_tasks(not_completed)
        while not_completed:
            completed, not_completed = \
                wait(not_completed, return_when="FIRST_COMPLETED")

            for future in completed:
                try:
                    result = future.result()
                except Exception as exp:  # pylint: disable=broad-except
                    result = exp
                task = self._future_key2task[future.key]
                self._task2result[task] = result

                yield task, result
                finished_tasks += 1
                # del ref to future in order to make dask gc its resources
                logger.debug("clean up task %s", task)
                logger.info(
                    "finished %s/%s", finished_tasks,
                    initial_task_count)
                del self._task2future[task]

            not_completed = self._schedule_tasks(not_completed)

        # clean up
        if len(self._task2future) > 0:
            logger.error("[BUG] Dask Executor's future q is not empty.")
        if len(self._task_queue) > 0:
            logger.error("[BUG] Dask Executor's task q is not empty.")

        self._task2future = {}
        self._future_key2task = {}
        self._task_queue = deque()
        self._task2result = {}

    def _set_task_result(self, task: Task, result: Any) -> None:
        self._task2result[task] = result

    def close(self) -> None:
        cluster = self._client.cluster
        self._client.shutdown()
        if cluster is not None:
            cluster.close()


def task_graph_status(
        task_graph: TaskGraph, task_cache: TaskCache,
        verbose: Optional[int]) -> bool:
    """Show the status of each task from the task graph."""
    id_col_len = max(len(t.task_id) for t in task_graph.tasks)
    id_col_len = min(120, max(50, id_col_len))
    columns = ["TaskID", "Status"]
    print(f"{columns[0]:{id_col_len}s} {columns[1]}")
    task2record = dict(task_cache.load(task_graph))
    for task in task_graph.tasks:
        record = task2record[task]
        status = record.type.name
        msg = f"{task.task_id:{id_col_len}s} {status}"
        is_error = record.type == CacheRecordType.ERROR
        if is_error and not verbose:
            msg += " (-v to see exception)"
        print(msg)
        if is_error and verbose:
            traceback.print_exception(
                None, value=record.error,
                tb=record.error.__traceback__,
                file=sys.stdout,
            )
    return True


def task_graph_run(
    task_graph: TaskGraph, executor: TaskGraphExecutor, keep_going: bool,
) -> bool:
    """Execute (runs) the task_graph with the given executor."""
    tasks_iter = executor.execute(task_graph)
    no_errors = True
    for task, result_or_error in tasks_iter:
        if isinstance(result_or_error, Exception):
            if keep_going:
                print(f"Task {task.task_id} failed with:",
                      file=sys.stderr)
                traceback.print_exception(
                    None, value=result_or_error,
                    tb=result_or_error.__traceback__,
                    file=sys.stdout,
                )
                no_errors = False
            else:
                raise result_or_error
    return no_errors


def task_graph_run_with_results(
    task_graph: TaskGraph, executor: TaskGraphExecutor,
) -> Generator[Any, None, None]:
    """Run a task graph, yielding the results from each task."""
    tasks_iter = executor.execute(task_graph)
    for _, result_or_error in tasks_iter:
        if isinstance(result_or_error, Exception):
            raise result_or_error
        yield result_or_error


def task_graph_all_done(task_graph: TaskGraph, task_cache: TaskCache) -> bool:
    """Check if the task graph is fully executed.

    When all tasks are already computed, the function returns True.
    If there are tasks, that need to run, the function returns False.
    """
    # pylint: disable=protected-access
    AbstractTaskGraphExecutor._check_for_cyclic_deps(task_graph)

    already_computed_tasks = {}
    for task_node, record in task_cache.load(task_graph):
        if record.type == CacheRecordType.COMPUTED:
            already_computed_tasks[task_node] = record.result

    for task_node in AbstractTaskGraphExecutor._in_exec_order(task_graph):
        if task_node not in already_computed_tasks:
            return False

    return True
