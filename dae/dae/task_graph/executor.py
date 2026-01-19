from __future__ import annotations

import logging
import multiprocessing as mp
import os
import pickle  # noqa: S403
import sys
import time
import traceback
from abc import abstractmethod
from collections import defaultdict, deque
from collections.abc import Callable, Generator, Iterator, Sequence
from concurrent.futures import Future as TPFuture
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import copy
from types import TracebackType
from typing import Any, cast

import fsspec
import matplotlib.pyplot as plt
import networkx
import psutil
from dask.distributed import Client, Future

from dae.task_graph.cache import CacheRecordType, NoTaskCache, TaskCache
from dae.task_graph.graph import Task, TaskGraph
from dae.task_graph.logging import (
    configure_task_logging,
    ensure_log_dir,
    safe_task_id,
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
    def _draw_di_graph(di_graph: networkx.DiGraph) -> None:
        plt.figure(figsize=(30, 15))
        pos = networkx.spring_layout(di_graph)
        networkx.draw(di_graph, pos, with_labels=True, arrows=True)
        plt.savefig("task_graph.png")
        plt.close()

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


class SequentialExecutor(AbstractTaskGraphExecutor):
    """A Task Graph Executor that executes task in sequential order."""

    def _await_tasks(self) -> Generator[tuple[Task, Any], None, None]:
        finished_tasks = 0
        initial_task_count = len(self._task_queue)

        while self._task_queue:
            selected_tasks = self._select_tasks_to_run(1)
            for task in selected_tasks:
                # handle tasks that use the output of other tasks
                params = copy(self._params)
                task_id = safe_task_id(task.task_id)
                params["task_id"] = task_id

                try:
                    result = self._exec(task.func, task.args, [], params)
                except Exception as exp:  # noqa: BLE001
                    # pylint: disable=broad-except
                    result = exp
                self._process_completed_task(task, result)

                finished_tasks += 1
                logger.debug("clean up task %s", task)
                logger.info(
                    "finished %s/%s", finished_tasks,
                    initial_task_count)

                del self._task_queue[task.task_id]

                yield task, result

        # all tasks have already executed. Let's clean the state.
        assert len(self._task_queue) == 0


class DaskExecutor(AbstractTaskGraphExecutor):
    """Execute tasks in parallel using Dask to do the heavy lifting."""

    def __init__(
        self, client: Client, task_cache: TaskCache = NO_TASK_CACHE,
        **kwargs: Any,
    ):
        super().__init__(task_cache, **kwargs)
        self._client = client
        self._task2future: dict[Task, Future] = {}
        self._future2task: dict[str, Task] = {}

    def _submit_task(self, task: Task) -> Future:
        assert len(task.deps) == 0
        assert not any(isinstance(arg, Task) for arg in task.args), \
            "Task has no dependencies to wait for."

        params = copy(self._params)
        task_id = safe_task_id(task.task_id)
        params["task_id"] = task_id

        future = self._client.submit(
            self._exec, task.func, task.args, [], params,
            key=task_id,
            pure=False,
        )
        if future is None:
            raise ValueError(
                f"unexpected dask executor return None: {task}, {task.args}, "
                f"{params}")
        assert future is not None

        self._task2future[task] = future
        self._future2task[str(future.key)] = task
        return future

    MIN_QUEUE_SIZE = 200

    def _queue_size(self) -> int:
        n_workers = cast(
            int,
            sum(self._client.ncores().values()))
        return max(self.MIN_QUEUE_SIZE, 4 * n_workers)

    def _available_slots(self, currently_running: int) -> int:
        return self._queue_size() - currently_running

    def _schedule_tasks(self, currently_running: set[Future]) -> set[Future]:
        start = time.time()
        tasks_to_run = self._select_tasks_to_run(
            self._available_slots(len(currently_running)))
        logger.debug("scheduling %d tasks", len(tasks_to_run))
        scheduled = 0
        for task in tasks_to_run:
            del self._task_queue[task.task_id]
            future = self._submit_task(task)
            currently_running.add(future)
            elapsed = time.time() - start
            scheduled += 1
            if elapsed > 10.0:
                logger.debug(
                    "scheduling took too long (%.2f sec), stopping",
                    elapsed)
                break

        elapsed = time.time() - start
        logger.debug(
            "scheduling %d tasks took %.2f sec", scheduled, elapsed)
        logger.debug("currently running %d tasks", len(currently_running))
        return currently_running

    def _await_tasks(self) -> Generator[tuple[Task, Any], None, None]:
        # pylint: disable=import-outside-toplevel
        from dask.distributed import wait

        not_completed: set[Future] = set()
        completed: deque[Future] = deque()
        initial_task_count = len(self._task_queue)
        finished_tasks = 0
        process = psutil.Process(os.getpid())
        current_memory_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(
            "executor memory usage: %.2f MB", current_memory_mb)

        not_completed = self._schedule_tasks(not_completed)
        while not_completed or self._task_queue:
            if len(completed) < self._queue_size() // 2:
                not_completed = self._schedule_tasks(not_completed)
            else:
                logger.debug(
                    "too many completed tasks (%d), processing them first",
                    len(completed))

            if not_completed:
                try:
                    new_completed, not_completed = wait(
                        not_completed,
                        return_when="FIRST_COMPLETED",
                        timeout=0.1,
                    )
                except TimeoutError:
                    new_completed = set()

            else:
                new_completed = set()

            for future in new_completed:
                completed.append(future)

            start = time.time()
            processed: list[tuple[Task, Any]] = []
            logger.debug("going to process %d completed tasks", len(completed))
            while completed:
                future = completed.popleft()
                task = self._future2task[str(future.key)]
                result_start = time.time()
                try:
                    result = future.result()
                except Exception as ex:  # noqa: BLE001
                    # pylint: disable=broad-except
                    result = ex
                result_elapsed = time.time() - result_start
                logger.debug(
                    "retrieving result for task %s took %.2f sec",
                    task.task_id, result_elapsed)

                self._process_completed_task(task, result)

                finished_tasks += 1
                processed.append((task, result))
                logger.info(
                    "finished %s/%s", finished_tasks,
                    initial_task_count)
                # del ref to future in order to make dask gc its resources
                del self._task2future[task]
                del self._future2task[future.key]

                elapsed = time.time() - start
                if elapsed > 2.0:
                    logger.debug(
                        "processing completed tasks took too long "
                        "(%.2f sec), stopping", elapsed)
                    break

            logger.debug("processed %d completed tasks", len(processed))
            start = time.time()
            yield from processed
            elapsed = time.time() - start
            logger.debug(
                "yielding %d completed tasks took %.2f sec",
                len(processed), elapsed)

        # clean up
        assert len(self._task2future) == 0, \
            "[BUG] Dask Executor's future queue is not empty."
        assert len(self._task_queue) == 0, \
            "[BUG] Dask Executor's task queue is not empty."

        self._task2future = {}
        self._future2task = {}
        assert len(self._task_queue) == 0

    def close(self) -> None:
        self._client.close()


class ThreadedTaskExecutor(AbstractTaskGraphExecutor):
    """Execute tasks in parallel using Dask to do the heavy lifting."""

    def __init__(
        self, task_cache: TaskCache = NO_TASK_CACHE,
        **kwargs: Any,
    ):
        super().__init__(task_cache, **kwargs)
        max_workers = kwargs.get("n_threads", os.cpu_count() or 1)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._task2future: dict[Task, TPFuture] = {}
        self._future2task: dict[TPFuture, Task] = {}

    def _submit_task(self, task: Task) -> TPFuture:
        assert len(task.deps) == 0
        assert not any(isinstance(arg, Task) for arg in task.args), \
            "Task has no dependencies to wait for."

        params = copy(self._params)
        task_id = safe_task_id(task.task_id)
        params["task_id"] = task_id

        future = self._executor.submit(
            self._exec_internal, task.func, task.args, [], params,
        )
        if future is None:
            raise ValueError(
                f"unexpected dask executor return None: {task}, {task.args}, "
                f"{params}")
        assert future is not None

        self._task2future[task] = future
        self._future2task[future] = task
        return future

    @staticmethod
    def _exec_internal(
        task_func: Callable, args: list, _deps: list, params: dict[str, Any],
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

    def _available_slots(self, currently_running: int) -> int:
        return max(0, 10_000 - currently_running)

    def _schedule_tasks(
        self, currently_running: set[TPFuture],
    ) -> set[TPFuture]:
        start = time.time()
        tasks_to_run = self._select_tasks_to_run(
            self._available_slots(len(currently_running)))
        logger.debug("scheduling %d tasks", len(tasks_to_run))
        for task in tasks_to_run:
            del self._task_queue[task.task_id]
            future = self._submit_task(task)
            currently_running.add(future)
            elapsed = time.time() - start
            if elapsed > 10.0:
                logger.debug(
                    "scheduling took too long (%.2f sec), stopping",
                    elapsed)
                break

        elapsed = time.time() - start
        logger.debug("currently running %d tasks", len(currently_running))
        return currently_running

    def _await_tasks(self) -> Generator[tuple[Task, Any], None, None]:
        not_completed: set[TPFuture] = set()
        completed: deque[TPFuture] = deque()
        initial_task_count = len(self._task_queue)
        finished_tasks = 0
        process = psutil.Process(os.getpid())
        current_memory_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(
            "executor memory usage: %.2f MB", current_memory_mb)

        not_completed = self._schedule_tasks(not_completed)
        while not_completed or self._task_queue:
            logger.info(
                "executor queue: %d tasks",
                self._executor._work_queue.qsize())  # noqa: SLF001
            not_completed = self._schedule_tasks(not_completed)

            for future in as_completed(not_completed):
                not_completed.remove(future)
                completed.append(future)

            start = time.time()
            processed: list[tuple[Task, Any]] = []
            logger.debug("going to process %d completed tasks", len(completed))
            while completed:
                future = completed.popleft()
                task = self._future2task[future]
                result_start = time.time()
                try:
                    result = future.result()
                except Exception as ex:  # noqa: BLE001
                    # pylint: disable=broad-except
                    result = ex
                result_elapsed = time.time() - result_start
                logger.debug(
                    "retrieving result for task %s took %.2f sec",
                    task.task_id, result_elapsed)

                self._process_completed_task(task, result)

                finished_tasks += 1
                processed.append((task, result))
                logger.info(
                    "finished %s/%s", finished_tasks,
                    initial_task_count)
                # del ref to future in order to make dask gc its resources
                del self._task2future[task]
                del self._future2task[future]

                elapsed = time.time() - start
                if elapsed > 2.0:
                    logger.debug(
                        "processing completed tasks took too long "
                        "(%.2f sec), stopping", elapsed)
                    break

            logger.debug("processed %d completed tasks", len(processed))
            start = time.time()
            yield from processed
            elapsed = time.time() - start
            logger.debug(
                "yielding %d completed tasks took %.2f sec",
                len(processed), elapsed)
        # clean up
        assert len(self._task2future) == 0, \
            "[BUG] Dask Executor's future queue is not empty."
        assert len(self._task_queue) == 0, \
            "[BUG] Dask Executor's task queue is not empty."

        self._task2future = {}
        self._future2task = {}
        assert len(self._task_queue) == 0

    def close(self) -> None:
        self._executor.shutdown()


def task_graph_run(
    task_graph: TaskGraph,
    executor: TaskGraphExecutor | None = None,
    *,
    keep_going: bool = False,
) -> bool:
    """Execute (runs) the task_graph with the given executor."""
    no_errors = True
    for result_or_error in task_graph_run_with_results(
            task_graph, executor, keep_going=keep_going):
        if isinstance(result_or_error, Exception):
            no_errors = False
    return no_errors


def task_graph_run_with_results(
    task_graph: TaskGraph, executor: TaskGraphExecutor | None = None,
    *,
    keep_going: bool = False,
) -> Generator[Any, None, None]:
    """Run a task graph, yielding the results from each task."""
    if executor is None:
        executor = SequentialExecutor()
    tasks_iter = executor.execute(task_graph)
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
            else:
                raise result_or_error
        yield result_or_error


def task_graph_all_done(task_graph: TaskGraph, task_cache: TaskCache) -> bool:
    """Check if the task graph is fully executed.

    When all tasks are already computed, the function returns True.
    If there are tasks, that need to run, the function returns False.
    """
    # pylint: disable=protected-access
    AbstractTaskGraphExecutor._check_for_cyclic_deps(  # noqa: SLF001
        task_graph)

    already_computed_tasks = {}
    for task_node, record in task_cache.load(task_graph):
        if record.type == CacheRecordType.COMPUTED:
            already_computed_tasks[task_node] = record.result

    for task_node in AbstractTaskGraphExecutor._in_exec_order(  # noqa: SLF001
            task_graph):
        if task_node not in already_computed_tasks:
            return False

    return True


def task_graph_status(
        task_graph: TaskGraph, task_cache: TaskCache,
        verbose: int | None) -> bool:
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
