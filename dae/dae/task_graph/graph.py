from __future__ import annotations

import logging
import multiprocessing as mp
from collections import defaultdict
from collections.abc import Callable, Generator, Sequence
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


def sync_tasks() -> None:
    return None


class TaskGraph:
    """An object representing a graph of tasks."""

    def __init__(self) -> None:
        self._lock = mp.Lock()
        self._tasks: dict[str, Task] = {}
        self._task_dependants: dict[str, set[str]] = defaultdict(set)
        self._done_tasks: dict[Task, Any] = {}

        self.input_files: list[str] = []

    @property
    def tasks(self) -> Sequence[Task]:
        """Return all tasks in the graph."""
        with self._lock:
            return list(self._tasks.values())

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
                TaskGraph._collect_task_deps(dep, task_set)

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
        if not networkx.is_directed_acyclic_graph(di_graph):
            raise ValueError("Cyclic dependencys in task graph detected")

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
            self._prune_dependants(dep_id)

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
                if task_id in self._tasks:
                    task = self._tasks.pop(task_id)
                    self._done_tasks[task] = result

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

    def __deepcopy__(self, memo: dict[int, Any]) -> TaskGraph:
        new_graph = TaskGraph()
        with self._lock:
            for task in self._tasks.values():
                new_deps = [
                    copy(memo[id(dep)]) if id(dep) in memo else dep
                    for dep in task.deps]
                new_task = Task(
                    task.task_id,
                    task.func,
                    copy(task.args),
                    new_deps,
                    copy(task.input_files),
                )
                memo[id(task)] = new_task
                new_graph._add_task(new_task)
        return new_graph
