from abc import abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(eq=False, frozen=True)
class TaskNode:
    """Represent one node in a TaskGraph together with its dependancies."""

    name: str
    func: Callable
    args: list[Any]
    deps: list["TaskNode"]


class TaskGraph:
    """An object representing a graph of tasks."""

    def __init__(self):
        self.nodes = []

    def create_task(self, name: str, func: Callable[..., Any], args: list,
                    deps: list[TaskNode]) -> TaskNode:
        """Create a new task and adds it to the graph.

        :param name: Name of the task (used for debugging purposes)
        :param func: Function to execute
        :param args: Arguments to that function
        :param deps: List of TaskNodes on which the current task depends
        :return TaskNode: The newly created task node in the graph
        """
        # tasks that use the output of other tasks as input should
        # have those other tasks as dependancies
        for arg in args:
            if isinstance(arg, TaskNode):
                deps.append(arg)
        node = TaskNode(name, func, args, deps)
        self.nodes.append(node)
        return node


class TaskGraphExecutor:
    @abstractmethod
    def execute(self, task_graph: TaskGraph):
        """Execute the graph."""


class AbstractTaskGraphExecutor(TaskGraphExecutor):
    """Executor that walks the graph in order that satisfies dependancies."""

    def execute(self, task_graph: TaskGraph) -> None:
        """Execute the graph."""
        self._check_for_cyclic_deps(task_graph)
        for task_node in self._in_exec_order(task_graph):
            self.queue_task(task_node)
        return self.await_tasks()

    @abstractmethod
    def queue_task(self, task_node: TaskNode) -> None:
        """Put the task on the execution queue."""

    @abstractmethod
    def await_tasks(self) -> None:
        """Wait for all queued tasks to finish."""

    def _in_exec_order(self, task_graph):
        visited = set()
        for node in task_graph.nodes:
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
        for node in task_graph.nodes:
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

    def __init__(self):
        self.task2result = {}

    def queue_task(self, task_node):
        # handle tasks that use the output of other tasks
        args = [self.task2result[arg] if isinstance(arg, TaskNode) else arg
                for arg in task_node.args]
        result = task_node.func(*args)
        self.task2result[task_node] = result

    def await_tasks(self):
        # all tasks have already been executed. Let's clean the state.
        self.task2result = {}


class DaskExecutor(AbstractTaskGraphExecutor):
    """Execute tasks in parallel using Dask to do the heavy lifting."""

    def __init__(self, client):
        self.client = client
        self.task2future = {}

    def queue_task(self, task_node):
        deps = [self.task2future[d] for d in task_node.deps]
        # handle tasks that use the output of other tasks
        args = [self.task2future[arg] if isinstance(arg, TaskNode) else arg
                for arg in task_node.args]
        future = self.client.submit(self._exec, task_node.func, args, deps)
        self.task2future[task_node] = future

    def await_tasks(self):
        # pylint: disable=import-outside-toplevel
        from dask.distributed import as_completed

        futures = list(self.task2future.values())
        self.task2future = {}
        for future in as_completed(futures):
            future.result()

    @staticmethod
    def _exec(task_func, args, _deps):
        return task_func(*args)
