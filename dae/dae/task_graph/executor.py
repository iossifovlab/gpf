from abc import abstractmethod
from copy import copy
from typing import Any, Iterator
import logging

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


class AbstractTaskGraphExecutor(TaskGraphExecutor):
    """Executor that walks the graph in order that satisfies dependancies."""

    def __init__(self, task_cache: TaskCache = NoTaskCache()):
        super().__init__()
        self._task_cache = task_cache

    def execute(self, task_graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        self._check_for_cyclic_deps(task_graph)

        self._task_cache.set_task_graph(task_graph)
        already_computed_tasks = {}
        for task_node in self._in_exec_order(task_graph):
            record = self._task_cache.get_record(task_node)
            if record.type == CacheRecordType.COMPUTED:
                already_computed_tasks[task_node] = record.result
                self._set_task_result(task_node, record.result)
            else:
                self._queue_task(task_node)
        return self.__await_tasks(already_computed_tasks)

    def __await_tasks(self, already_computed_tasks) \
            -> Iterator[tuple[Task, Any]]:
        for task_node, result in already_computed_tasks.items():
            yield task_node, result
        for task_node, result in self._await_tasks():
            is_error = isinstance(result, BaseException)
            self._task_cache.cache(task_node, is_error, result)
            yield task_node, result

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
        visited = set()
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
        visited = set()
        stack = []
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
        self._future2task = {}
        self._finished_futures = set()
        self._task2result = {}

    def _queue_task(self, task_node):
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
        self._future2task[future.key] = task_node

    def _await_tasks(self):
        # pylint: disable=import-outside-toplevel
        from dask.distributed import as_completed

        assert len(self._finished_futures) == 0, "Cannot call execute twice"

        futures = list(self._task2future.values())
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as exp:  # pylint: disable=broad-except
                result = exp
            self._finished_futures.add(future.key)
            yield self._future2task[future.key], result

        # clean up
        self._task2future = {}
        self._future2task = {}
        self._finished_futures = set()
        self._task2result = {}

    def _set_task_result(self, task, result):
        self._task2result[task] = result

    def get_active_tasks(self):
        res = []
        for task, future in self._task2future.items():
            all_deps_satisfied = all(
                self._task2future[dep].key in self._finished_futures
                for dep in task.deps if dep in self._task2future
            )
            if future.key not in self._finished_futures and all_deps_satisfied:
                res.append(task)
        return res

    def _get_future_or_result(self, task):
        future = self._task2future.get(task)
        return future if future else self._task2result[task]

    @staticmethod
    def _exec(task_func, args, _deps):
        return task_func(*args)
