from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Iterator
from types import TracebackType
from typing import Any

from dae.task_graph.graph import Task, TaskGraph

logger = logging.getLogger(__name__)


class TaskGraphExecutor:
    """Class that executes a task graph."""

    @abstractmethod
    def execute(self, graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        """Start executing the graph.

        Return an iterator that yields the task in the graph
        after they are executed.

        This is not necessarily in DFS or BFS order.
        This is not even the order in which these tasks are executed.

        The only guarantee is that when a task is returned its execution
        is already finished.
        """

    def __enter__(self) -> TaskGraphExecutor:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        self.close()
        return exc_type is None

    @abstractmethod
    def close(self) -> None:
        """Clean-up any resources used by the executor."""
