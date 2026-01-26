from __future__ import annotations

import logging
import multiprocessing as mp
from collections import defaultdict
from collections.abc import Callable, Generator, Iterable, Sequence
from copy import copy
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Task:
    """Represent one node in a TaskGraph together with its dependencies."""

    task_id: str
    func: Callable
    args: list[Any]
    deps: list[Task]
    input_files: list[str]

    def __repr__(self) -> str:
        deps = ",".join(dep.task_id for dep in self.deps)
        in_files = ",".join(self.input_files)
        return f"Task(id={self.task_id}, deps={deps}, in_files={in_files})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Task):
            return False
        return self.task_id == other.task_id

    def __hash__(self) -> int:
        return hash(self.task_id)


class TaskGraph:
    """An object representing a graph of tasks."""

    def __init__(self) -> None:
        self.tasks: list[Task] = []
        self.input_files: list[str] = []
        self._task_ids: set[str] = set()

    def create_task(
        self, task_id: str, func: Callable[..., Any], *,
        args: list,
        deps: list[Task],
        input_files: list[str] | None = None,
    ) -> Task:
        """Create a new task and add it to the graph.

        :param name: Name of the task (used for debugging purposes)
        :param func: Function to execute
        :param args: Arguments to that function
        :param deps: List of TaskNodes on which the current task depends
        :param input_files: Files that were used to build the graph itself
        :return TaskNode: The newly created task node in the graph
        """
        if len(task_id) > 200:
            logger.warning("task id is too long %s: %s", len(task_id), task_id)
            logger.warning("truncating task id to 200 symbols")
            task_id = task_id[:200]

        if task_id in self._task_ids:
            raise ValueError(f"Task with id='{task_id}' already in graph")

        # tasks that use the output of other tasks as input should
        # have those other tasks as dependancies
        deps = copy(deps)
        for arg in args:
            if isinstance(arg, Task):
                deps.append(arg)
        node = Task(task_id, func, args, deps, input_files or [])
        self.tasks.append(node)
        self._task_ids.add(task_id)
        return node

    def prune(self, ids_to_keep: Iterable[str]) -> TaskGraph:
        """Prune tasks which are not in ids_to_keep or in their deps.

        tasks ids which are in ids_to_keep but not in the graph are simply
        assumed to have already been removed and no error is raised.
        """
        ids_to_keep = set(ids_to_keep)
        ids_not_found = ids_to_keep - self._task_ids
        if ids_not_found:
            raise KeyError(ids_not_found)

        tasks_to_keep: set[str] = set()
        for task in self.tasks:
            if task.task_id in ids_to_keep:
                tasks_to_keep.add(task.task_id)
                self._add_task_deps(task, tasks_to_keep)

        new_tasks = [t for t in self.tasks if t.task_id in tasks_to_keep]
        res = TaskGraph()
        res.tasks = new_tasks
        res.input_files = self.input_files
        res._task_ids |= tasks_to_keep
        return res

    @staticmethod
    def _add_task_deps(task: Task, task_set: set[str]) -> None:
        for dep in task.deps:
            if dep.task_id not in task_set:
                task_set.add(dep.task_id)
                TaskGraph._add_task_deps(dep, task_set)


def sync_tasks() -> None:
    return None


class TaskGraph2:
    """An object representing a graph of tasks."""

    def __init__(self) -> None:
        self._lock = mp.Lock()
        self._tasks: dict[str, Task] = {}
        self._task_dependants: dict[str, set[str]] = defaultdict(set)
        self._done_tasks: dict[Task, Any] = {}

        self.input_files: list[str] = []

    def add_task(self, task: Task) -> None:
        """Add a new task to the graph.

        :param task: Task to add
        """
        with self._lock:
            self._add_task(task)

    def _add_task(self, task: Task) -> None:
        if task.task_id in self._tasks:
            raise ValueError(
                f"Task with id='{task.task_id}' already in graph")

        self._tasks[task.task_id] = task
        for dep in task.deps:
            self._task_dependants[dep.task_id].add(task.task_id)

    def create_task(
        self, task_id: str, func: Callable[..., Any], *,
        args: list,
        deps: list[Task],
        input_files: list[str] | None = None,
    ) -> Task:
        """Create a new task and add it to the graph.

        :param name: Name of the task (used for debugging purposes)
        :param func: Function to execute
        :param args: Arguments to that function
        :param deps: List of TaskNodes on which the current task depends
        :param input_files: Files that were used to build the graph itself
        :return TaskNode: The newly created task node in the graph
        """
        if len(task_id) > 200:
            logger.warning("task id is too long %s: %s", len(task_id), task_id)
            logger.warning("truncating task id to 200 symbols")
            task_id = task_id[:200]

        with self._lock:
            if task_id in self._tasks:
                raise ValueError(f"Task with id='{task_id}' already in graph")

        # tasks that use the output of other tasks as input should
        # have those other tasks as dependancies
        deps = copy(deps)
        for arg in args:
            if isinstance(arg, Task):
                deps.append(arg)
        task = Task(task_id, func, args, deps, input_files or [])
        self.add_task(task)
        return task

    @staticmethod
    def _collect_task_deps(task: Task, task_set: set[str]) -> None:
        for dep in task.deps:
            if dep.task_id not in task_set:
                task_set.add(dep.task_id)
                TaskGraph2._collect_task_deps(dep, task_set)

    @staticmethod
    def from_task_graph(task_graph: TaskGraph) -> TaskGraph2:
        """Create TaskGraph2 from TaskGraph."""
        res = TaskGraph2()
        res.input_files = task_graph.input_files
        for task in task_graph.tasks:
            res.add_task(task)
        return res

    def ready_tasks(self) -> Sequence[Task]:
        """Return tasks which have no dependencies."""
        result = []
        with self._lock:
            for task in self._topological_order():
                if task.deps:
                    break
                result.append(task)
            for task in result:
                del self._tasks[task.task_id]

        return result

    def _topological_order(self) -> Generator[Task, None, None]:
        """Return tasks in topological order."""
        # pylint: disable=import-outside-toplevel
        import networkx
        di_graph = networkx.DiGraph()
        nodes: list[str] = list(self._tasks.keys())
        di_graph.add_nodes_from(sorted(nodes))

        for task in self._tasks.values():
            for dep in task.deps:
                di_graph.add_edge(dep.task_id, task.task_id)

        for task_id in networkx.topological_sort(di_graph):
            if task_id not in self._tasks:
                continue
            yield self._tasks[task_id]

    def topological_order(self) -> Sequence[Task]:
        """Return tasks in topological order."""
        with self._lock:
            return list(self._topological_order())

    def _prune_dependants(self, task_id: str) -> None:
        dependents = self._task_dependants.get(task_id, set())
        for dep_id in dependents:
            logger.debug("pruning dependent task %s", dep_id)
            if dep_id not in self._tasks:
                continue
            del self._tasks[dep_id]

    def _reconfigure_task_deps(
        self, task: Task,
        completed_task_id: str,
        completed_result: Any,
    ) -> Task:
        args = []
        for arg in task.args:
            if isinstance(arg, Task) and arg.task_id == completed_task_id:
                arg = completed_result
            args.append(arg)

        deps = []
        for dep in task.deps:
            if dep.task_id == completed_task_id:
                continue
            deps.append(dep)

        return Task(
            task.task_id,
            task.func,
            args,
            deps,
            task.input_files,
        )

    def get_task(self, task_id: str) -> Task:
        """Get task by its id.

        :param task_id: Id of the task to get
        :return: Task with the given id
        """
        with self._lock:
            return self._tasks[task_id]

    def process_completed_tasks(
        self, task_result: Sequence[tuple[str, Any]],
    ) -> None:
        """Process a completed task.

        :param task: Completed task
        """
        with self._lock:
            for task_id, result in task_result:
                if isinstance(result, BaseException):
                    self._prune_dependants(task_id)
                    return
                task_dependants = self._task_dependants.get(task_id, set())
                for dep_id in task_dependants:
                    if dep_id not in self._tasks:
                        continue
                    dep_task = self._tasks[dep_id]
                    dep_task = self._reconfigure_task_deps(
                        dep_task, task_id, result)
                    self._tasks[dep_id] = dep_task
                if task_id in self._task_dependants:
                    del self._task_dependants[task_id]

    def __len__(self) -> int:
        with self._lock:
            return len(self._tasks)

    def empty(self) -> bool:
        """Check if the graph is empty."""
        with self._lock:
            return len(self._tasks) == 0
