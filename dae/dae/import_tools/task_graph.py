from abc import abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Any, Callable


class TaskGraph:
    def __init__(self):
        self.nodes = []

    def create_task(self, name, func, args, deps):
        node = TaskNode(name, func, args, deps)
        self.nodes.append(node)
        return node


class TaskGraphExecutor:
    def execute(self, task_graph):
        self._check_for_cyclic_deps(task_graph)
        for task_node in self._in_exec_order(task_graph):
            self.queue_task(task_node)
        return self.await_tasks()

    @abstractmethod
    def queue_task(self, task_node):
        pass

    @abstractmethod
    def await_tasks(self):
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
    @abstractmethod
    def queue_task(self, task_node):
        task_node.func(*task_node.args)

    def await_tasks(self):
        pass
