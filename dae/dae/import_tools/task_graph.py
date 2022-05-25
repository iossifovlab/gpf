from abc import abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Any, Callable


class TaskGraph:
    """An object representing a graph of tasks"""
    def __init__(self):
        self.nodes = []

    def create_task(self, name, func, args, deps):
        """Creates a new task and adds it to the graph

        :param name: Name of the task (used for debugging purposes)
        :param func: Function to execute
        :param args: Arguments to that function
        :param deps: List of TaskNodes on which the current task depends
        :return TaskNode: The newly created task node in the graph
        """
        node = TaskNode(name, func, args, deps)
        self.nodes.append(node)
        return node


class TaskGraphExecutor:
    def execute(self, task_graph):
        """Executes the graph"""
        self._check_for_cyclic_deps(task_graph)
        for task_node in self._in_exec_order(task_graph):
            self.queue_task(task_node)
        return self.await_tasks()

    @abstractmethod
    def queue_task(self, task_node):
        """Put the task on the execution queue"""
        pass

    @abstractmethod
    def await_tasks(self):
        """Wait for all queued tasks to finish"""
        pass

    def _in_exec_order(self, task_graph):
        visited = set()
        for n in task_graph.nodes:
            yield from self._node_in_exec_order(n, visited)

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

        for n in node.deps:
            if n not in visited:
                return self._find_cycle(n, visited, stack)
            elif n in stack:
                return copy(stack)

        stack.pop()


@dataclass(eq=False, frozen=True)
class TaskNode:
    name: str
    func: Callable
    args: list[Any]
    deps: list['TaskNode']


class SequentialExecutor(TaskGraphExecutor):
    """A Task Graph Executor that executes task in a sequential order"""
    def queue_task(self, task_node):
        task_node.func(*task_node.args)

    def await_tasks(self):
        pass


class DaskExecutor(TaskGraphExecutor):
    """A Task Graph Executor that executes task in parallel using
    Dask to do the heavy lifting"""
    def __init__(self, client):
        self.client = client
        self.task2future = {}

    def queue_task(self, task_node):
        deps = [self.task2future[d] for d in task_node.deps]
        future = self.client.submit(self._exec, task_node, *deps)
        self.task2future[task_node] = future

    def await_tasks(self):
        from dask.distributed import as_completed

        futures = list(self.task2future.values())
        self.task2future = {}
        for f in as_completed(futures):
            f.result()

    @staticmethod
    def _exec(task_node, *deps):
        task_node.func(*task_node.args)
