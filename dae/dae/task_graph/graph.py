from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional


@dataclass(eq=False, frozen=True)
class Task:
    """Represent one node in a TaskGraph together with its dependancies."""

    task_id: str
    func: Callable
    args: list[Any]
    deps: list[Task]
    input_files: list[str]

    def __repr__(self):
        deps = ",".join(dep.task_id for dep in self.deps)
        in_files = ",".join(self.input_files)
        return f"Task(id={self.task_id}, deps={deps}, in_files={in_files})"


class TaskGraph:
    """An object representing a graph of tasks."""

    def __init__(self):
        self.tasks: list[Task] = []
        self.input_files: list[str] = []
        self._task_ids: set[str] = set()

    def create_task(self, task_id: str, func: Callable[..., Any], args: list,
                    deps: list[Task],
                    input_files: Optional[list[str]] = None) -> Task:
        """Create a new task and add it to the graph.

        :param name: Name of the task (used for debugging purposes)
        :param func: Function to execute
        :param args: Arguments to that function
        :param deps: List of TaskNodes on which the current task depends
        :param input_files: Files that were used to build the graph itself
        :return TaskNode: The newly created task node in the graph
        """
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

    def prune(self, ids_to_keep: Iterable[str]):
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
    def _add_task_deps(task, task_set):
        for dep in task.deps:
            if dep not in task_set:
                task_set.add(dep.task_id)
                TaskGraph._add_task_deps(dep, task_set)
