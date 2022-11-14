from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(eq=False, frozen=True)
class Task:
    """Represent one node in a TaskGraph together with its dependancies."""

    name: str
    func: Callable
    args: list[Any]
    deps: list[Task]
    input_files: list[str]


class TaskGraph:
    """An object representing a graph of tasks."""

    def __init__(self):
        self.nodes = []
        self.input_files = []

    def create_task(self, name: str, func: Callable[..., Any], args: list,
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
        # tasks that use the output of other tasks as input should
        # have those other tasks as dependancies
        deps = copy(deps)
        for arg in args:
            if isinstance(arg, Task):
                deps.append(arg)
        node = Task(name, func, args, deps, input_files or [])
        self.nodes.append(node)
        return node
