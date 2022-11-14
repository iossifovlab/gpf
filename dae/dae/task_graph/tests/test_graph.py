import pytest
from dae.task_graph.graph import TaskGraph


def test_creating_two_tasks_with_the_same_id():
    graph = TaskGraph()
    graph.create_task("ID", lambda: None, [], [])
    with pytest.raises(ValueError):
        graph.create_task("ID", lambda: None, [], [])
