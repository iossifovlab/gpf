# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pytest
from dae.task_graph.graph import TaskGraph


def test_creating_two_tasks_with_the_same_id() -> None:
    graph = TaskGraph()
    graph.create_task("ID", lambda: None, args=[], deps=[])
    with pytest.raises(ValueError):  # noqa
        graph.create_task("ID", lambda: None, args=[], deps=[])
