import logging
from collections.abc import Iterator
from copy import copy
from typing import Any

from dae.task_graph.base_executor import TaskGraphExecutorBase
from dae.task_graph.cache import NoTaskCache
from dae.task_graph.graph import Task, TaskGraph
from dae.task_graph.logging import (
    safe_task_id,
)

NO_TASK_CACHE = NoTaskCache()
logger = logging.getLogger(__name__)


class SequentialExecutor(TaskGraphExecutorBase):
    """A Task Graph Executor that executes task in sequential order."""

    def _execute(self, graph: TaskGraph) -> Iterator[tuple[Task, Any]]:
        finished_tasks = 0
        initial_task_count = len(graph)

        while not graph.empty():
            ready_tasks = list(graph.ready_tasks())
            for task in ready_tasks:
                # handle tasks that use the output of other tasks
                params = copy(self._params)
                task_id = safe_task_id(task.task_id)
                params["task_id"] = task_id

                try:
                    result = self._exec(task.func, task.args, params)
                except Exception as exp:  # noqa: BLE001
                    # pylint: disable=broad-except
                    result = exp
                graph.process_completed_tasks([(task.task_id, result)])

                finished_tasks += 1
                logger.debug("clean up task %s", task)
                logger.info(
                    "finished %s/%s", finished_tasks,
                    initial_task_count)

                yield task, result

        # all tasks have already executed. Let's clean the state.
        assert len(graph) == 0

    def close(self) -> None:
        """Close the executor and release resources."""
