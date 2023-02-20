import sys
import logging
import traceback
from abc import abstractmethod
from copy import copy
from typing import Any, Iterator
from typing import Optional
from toolz.itertoolz import partition_all

from dae.task_graph.graph import TaskGraph, Task
from dae.task_graph.cache import TaskCache, NoTaskCache, CacheRecordType


logger = logging.getLogger(__file__)


class TaskGraphExecutor:
    """Class that executes a task graph."""

    @abstractmethod
    def execute(self, task_graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        """Start executing the graph.

        Return an iterator that yields the task in the graph as they finish not
        nessessarily in DFS or BFS order.
        """

    @abstractmethod
    def get_active_tasks(self) -> list[Task]:
        """Return the list of tasks currently being processed."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abstractmethod
    def close(self):
        """Clean-up any resources used by the executor."""


class AbstractTaskGraphExecutor(TaskGraphExecutor):
    """Executor that walks the graph in order that satisfies dependancies."""

    def __init__(self, task_cache: TaskCache = NoTaskCache()):
        super().__init__()
        self._task_cache = task_cache
        self._executing = False

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

    def _yield_task_results(self, already_computed_tasks) \
            -> Iterator[tuple[Task, Any]]:
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

    def _in_exec_order(self, task_graph):
        visited: set[Task] = set()
        for node in task_graph.tasks:
            yield from self._node_in_exec_order(node, visited)

    def _node_in_exec_order(self, node, visited):
        if node in visited:
            return
        visited.add(node)
        for dep in node.deps:
            yield from self._node_in_exec_order(dep, visited)
        yield node

    def _check_for_cyclic_deps(self, task_graph):
        visited: set[Task] = set()
        stack: list[Task] = []
        for node in task_graph.tasks:
            if node not in visited:
                cycle = self._find_cycle(node, visited, stack)
                if cycle is not None:
                    raise ValueError(f"Cyclic dependancy {cycle}")

    def _find_cycle(self, node, visited, stack):
        visited.add(node)
        stack.append(node)

        for dep in node.deps:
            if dep not in visited:
                return self._find_cycle(dep, visited, stack)
            if dep in stack:
                return copy(stack)

        stack.pop()
        return None

    def close(self):
        pass


class SequentialExecutor(AbstractTaskGraphExecutor):
    """A Task Graph Executor that executes task in sequential order."""

    def __init__(self, task_cache=NoTaskCache()):
        super().__init__(task_cache)
        self._task_queue = []
        self._task2result = {}

    def _queue_task(self, task_node):
        self._task_queue.append(task_node)

    def _await_tasks(self):
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
            try:
                result = task_node.func(*args)
            except Exception as exp:  # pylint: disable=broad-except
                result = exp
                is_error = True
            if not is_error:
                self._task2result[task_node] = result
            yield task_node, result

        # all tasks have already executed. Let's clean the state.
        self._task_queue = []
        self._task2result = {}

    def _set_task_result(self, task, result):
        self._task2result[task] = result

    def get_active_tasks(self):
        for task_node in self._task_queue:
            if task_node not in self._task2result:
                return [task_node]
        return []


class DaskExecutor(AbstractTaskGraphExecutor):
    """Execute tasks in parallel using Dask to do the heavy lifting."""

    def __init__(self, client, task_cache=NoTaskCache()):
        super().__init__(task_cache)
        self._client = client
        self._task2future = {}
        self._future_key2task = {}
        self._finished_future_keys = set()
        self._task2result = {}
        self._task_queue = []

    def _queue_task(self, task_node):
        self._task_queue.append(task_node)

    def _submit_task(self, task_node):
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

        future = self._client.submit(self._exec, task_node.func, args, deps,
                                     pure=False)
        self._task2future[task_node] = future
        self._future_key2task[future.key] = task_node

    def _await_tasks(self):
        # pylint: disable=import-outside-toplevel
        from dask.distributed import as_completed

        assert len(self._finished_future_keys) == 0, "Don't call execute twice"
        for tasks in partition_all(500, self._task_queue):
            for task_node in tasks:
                self._submit_task(task_node)

            for future in as_completed(list(self._task2future.values())):
                try:
                    result = future.result()
                except Exception as exp:  # pylint: disable=broad-except
                    result = exp
                self._finished_future_keys.add(future.key)
                task = self._future_key2task[future.key]
                self._task2result[task] = result

                yield task, result

                # del ref to future in order to make dask gc its resources
                logger.debug("clean up task %s", task)

            self._task2future = {}

        # clean up
        if len(self._task2future) > 0:
            logger.error("[BUG] Dask Executor's future q is not empty.")
        self._task2future = {}
        self._future_key2task = {}
        self._finished_future_keys = set()
        self._task_queue = []
        self._task2result = {}

    def _set_task_result(self, task, result):
        self._task2result[task] = result

    def get_active_tasks(self):
        for task_node in self._task_queue:
            if task_node not in self._task2result:
                return [task_node]
        return []

    def _get_future_or_result(self, task):
        future = self._task2future.get(task)
        return future if future else self._task2result[task]

    @staticmethod
    def _exec(task_func, args, _deps):
        return task_func(*args)

    def close(self):
        self._client.close()
        cluster = self._client.cluster
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
                etype=None, value=record.error,
                tb=record.error.__traceback__,
                file=sys.stdout
            )
    return True


def task_graph_run(
    task_graph: TaskGraph, executor: TaskGraphExecutor, keep_going: bool
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
                    etype=None, value=result_or_error,
                    tb=result_or_error.__traceback__
                )
                no_errors = False
            else:
                raise result_or_error
    return no_errors
