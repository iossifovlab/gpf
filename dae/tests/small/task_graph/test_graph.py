# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pytest

from dae.task_graph.graph import TaskGraph


def test_creating_two_tasks_with_the_same_id() -> None:
    graph = TaskGraph()
    graph.create_task("ID", lambda: None, [], [])
    with pytest.raises(ValueError):
        graph.create_task("ID", lambda: None, [], [])


def test_pruning() -> None:
    graph = _create_simple_graph()
    pruned_graph = graph.prune(ids_to_keep=["3"])
    assert len(pruned_graph.tasks) == 2
    pruned_ids = {t.task_id for t in pruned_graph.tasks}
    assert pruned_ids == {"1", "3"}
    assert pruned_graph._task_ids == {"1", "3"}
    assert pruned_graph.input_files == ["file1", "file2"]


def test_pruning_non_existent_ids() -> None:
    graph = _create_simple_graph()
    with pytest.raises(KeyError):
        graph.prune(ids_to_keep=["non-existant id"])


def _create_simple_graph() -> TaskGraph:
    graph = TaskGraph()
    graph.input_files.extend(["file1", "file2"])
    first_task = graph.create_task("1", lambda: None, [], [])
    mid_tasks = []
    for i in range(2, 10):
        mid_tasks.append(
            graph.create_task(str(i), lambda: None, [], [first_task]),
        )
    graph.create_task("final", lambda: None, [], mid_tasks)

    return graph
