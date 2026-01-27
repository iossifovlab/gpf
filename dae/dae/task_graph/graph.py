from __future__ import annotations

import logging
import multiprocessing as mp
from collections import defaultdict
from collections.abc import Callable, Generator, Sequence
from copy import copy
from dataclasses import dataclass
from types import TracebackType
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=True, unsafe_hash=True, order=True)
class Task:
    """Represent one node in a TaskGraph together with its dependencies."""

    task_id: str


@dataclass(frozen=True)
class TaskDesc:
    """Represent an immutable full task description with all its properties."""
    task: Task
    func: Callable
    args: list[Any]
    deps: list[Task]
    input_files: list[str]

    @staticmethod
    def _from_task_node(task_node: _Task) -> TaskDesc:
        return TaskDesc(
            task=task_node.task,
            func=task_node.func,
            args=task_node.args,
            deps=task_node.deps,
            input_files=task_node.input_files,
        )


class _Task:
    __slots__ = ("args", "deps", "func", "input_files", "task")

    def __init__(
        self, task_id: str | Task,
        func: Callable,
        args: list[Any],
        deps: list[Task],
        input_files: list[str],
    ) -> None:
        if isinstance(task_id, str):
            task_id = Task(task_id)
        self.task: Task = task_id
        self.func = func
        self.args = args
        self.deps: list[Task] = deps
        self.input_files: list[str] = input_files

    def __repr__(self) -> str:
        result = [
            f"id={self.task.task_id}, "
            f"func={self.func}, "
            f"args={self.args}",
        ]
        if self.deps:
            result.append(f"deps={[dep.task_id for dep in self.deps]})")
        if self.input_files:
            result.append(f"input_files={self.input_files})")
        return f"Task({', '.join(result)})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _Task):
            return False
        return self.task == other.task

    def __hash__(self) -> int:
        return hash(self.task)


def sync_tasks() -> None:
    return None


class TaskGraph:
    """An object representing a graph of tasks."""

    def __init__(self) -> None:
        self._lock = mp.Lock()
        self._tasks: dict[Task, _Task] = {}
        self._task_dependants: dict[Task, set[Task]] = defaultdict(set)

        self.input_files: list[str] = []

    @property
    def tasks(self) -> Sequence[Task]:
        """Return all tasks in the graph."""
        with self._lock:
            return list(self._tasks.keys())

    def _add_task(self, task: _Task) -> None:
        if task.task in self._tasks:
            raise ValueError(
                f"Task with id='{task.task}' already in graph")

        self._tasks[task.task] = task
        for dep in task.deps:
            self._task_dependants[dep].add(task.task)

    def create_task(
        self, task_id: str, func: Callable[..., Any], *,
        args: Sequence,
        deps: Sequence[Task],
        input_files: Sequence[str] | None = None,
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

        task = Task(task_id)
        with self._lock:
            if task in self._tasks:
                raise ValueError(f"Task with id='{task_id}' already in graph")

        # tasks that use the output of other tasks as input should
        # have those other tasks as dependancies
        deps = list(deps)
        for arg in args:
            if isinstance(arg, Task):
                deps.append(arg)
        self._add_task(_Task(
            task, func, list(args), deps,
            list(input_files) if input_files is not None else []))
        return task

    def _collect_task_deps(
        self,
        task: _Task,
        task_set: set[Task],
    ) -> None:
        for dep in task.deps:
            if dep not in task_set:
                task_set.add(dep)
                dep_task = self._tasks[dep]
                self._collect_task_deps(dep_task, task_set)

    def ready_tasks(self) -> Sequence[Task]:
        """Return tasks which have no dependencies."""
        result = []
        with self._lock:
            for t in self._topological_order():
                if t.deps:
                    break
                result.append(t.task)
        return result

    def get_task_desc(self, task: Task) -> TaskDesc:
        """Get full task description for a given task."""
        with self._lock:
            if task not in self._tasks:
                raise ValueError(f"task {task} not in graph")
            task_node = self._tasks[task]
            return TaskDesc._from_task_node(task_node)  # noqa: SLF001

    def extract_tasks(
            self, selected_tasks: Sequence[Task],
    ) -> Sequence[TaskDesc]:
        """Collects tasks from the task graph and and removes them."""
        result = []
        with self._lock:
            for task in selected_tasks:
                if task not in self._tasks:
                    raise ValueError(f"task {task} not in graph")
                result.append(
                    TaskDesc._from_task_node(self._tasks[task]))  # noqa: SLF001
                del self._tasks[task]
        return result

    def _topological_order(self) -> Generator[_Task, None, None]:
        """Return tasks in topological order."""
        # pylint: disable=import-outside-toplevel
        import networkx
        di_graph = networkx.DiGraph()
        nodes: list[Task] = list(self._tasks.keys())
        di_graph.add_nodes_from(sorted(nodes))

        for task in self._tasks.values():
            for dep in task.deps:
                di_graph.add_edge(dep, task.task)
        if not networkx.is_directed_acyclic_graph(di_graph):
            raise ValueError("Cyclic dependencys in task graph detected")

        for task_id in networkx.topological_sort(di_graph):
            if task_id not in self._tasks:
                continue
            yield self._tasks[task_id]

    def topological_order(self) -> Sequence[Task]:
        """Return tasks in topological order."""
        with self._lock:
            return [t.task for t in self._topological_order()]

    def _prune_dependants(self, task_id: Task) -> None:
        dependents = self._task_dependants.get(task_id, set())
        for dep_id in dependents:
            logger.debug("pruning dependent task %s", dep_id)
            if dep_id not in self._tasks:
                continue
            del self._tasks[dep_id]
            self._prune_dependants(dep_id)

    def _reconfigure_task_deps(
        self, task: _Task,
        completed_task_id: Task,
        completed_result: Any,
    ) -> None:
        args = []
        for arg in task.args:
            if isinstance(arg, Task) and arg == completed_task_id:
                arg = completed_result
            args.append(arg)

        deps = []
        for dep in task.deps:
            if dep == completed_task_id:
                continue
            deps.append(dep)

        task.args = args
        task.deps = deps

    def process_completed_tasks(
        self, task_result: Sequence[tuple[Task, Any]],
    ) -> None:
        """Process a completed task.

        :param task: Completed task
        """
        with self._lock:
            for task_id, result in task_result:
                if task_id in self._tasks:
                    self._tasks.pop(task_id)

                if isinstance(result, BaseException):
                    self._prune_dependants(task_id)
                    return
                task_dependants = self._task_dependants.get(task_id, set())
                for dep_id in task_dependants:
                    if dep_id not in self._tasks:
                        continue
                    dep_task = self._tasks[dep_id]
                    self._reconfigure_task_deps(
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
                new_task = _Task(
                    task.task,
                    task.func,
                    copy(task.args),
                    new_deps,
                    copy(task.input_files),
                )
                memo[id(task)] = new_task
                new_graph._add_task(new_task)
        return new_graph

    def get_task_deps(self, task: Task) -> list[Task]:
        """Get dependancies of a task suitable for dask executor."""
        with self._lock:
            if task not in self._tasks:
                raise ValueError(f"task {task} not in graph")
            task_node = self._tasks[task]
            return copy(task_node.deps)

    def __enter__(self) -> dict[Task, _Task]:
        self._lock.acquire()
        return self._tasks

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self._lock.release()
        return exc_type is None

    def prune(self, tasks_to_keep: Sequence[Task | str]) -> None:
        """Prune to keep the specified tasks and their dependencies."""
        with self._lock:
            tasks_set: set[Task] = set()
            for task in tasks_to_keep:
                if isinstance(task, str):
                    task = Task(task)
                if task not in self._tasks:
                    raise ValueError(f"task {task} not in graph")
                tasks_set.add(task)
                task_node = self._tasks[task]
                self._collect_task_deps(task_node, tasks_set)

            pruned_tasks = {
                task_id: task_node
                for task_id, task_node in self._tasks.items()
                if task_id in tasks_set
            }
            self._tasks = pruned_tasks
