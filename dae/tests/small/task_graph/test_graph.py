# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pytest
from dae.task_graph.graph import TaskGraph


def test_creating_two_tasks_with_the_same_id() -> None:
    graph = TaskGraph()
    graph.create_task("ID", lambda: None, args=[], deps=[])
    with pytest.raises(ValueError):  # noqa
        graph.create_task("ID", lambda: None, args=[], deps=[])


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


def test_add_task_deps_collects_all_dependencies() -> None:
    graph = _create_simple_graph()
    final_task = next(task for task in graph.tasks if task.task_id == "final")

    collected = {"final"}
    TaskGraph._add_task_deps(final_task, collected)

    expected = {"final", *(str(i) for i in range(1, 10))}
    assert collected == expected


def test_add_task_deps_preserves_existing_entries() -> None:
    graph = TaskGraph()
    root = graph.create_task("root", lambda: None, args=[], deps=[])
    mid = graph.create_task("mid", lambda: None, args=[], deps=[root])
    leaf = graph.create_task("leaf", lambda: None, args=[], deps=[mid])

    collected = {"leaf", "root"}
    TaskGraph._add_task_deps(leaf, collected)

    assert collected == {"leaf", "root", "mid"}


def _create_simple_graph() -> TaskGraph:
    graph = TaskGraph()
    graph.input_files.extend(["file1", "file2"])
    first_task = graph.create_task("1", lambda: None, args=[], deps=[])
    mid_tasks = [
        graph.create_task(
            str(i), lambda: None, args=[], deps=[first_task])
        for i in range(2, 10)
    ]
    graph.create_task("final", lambda: None, args=[], deps=mid_tasks)

    return graph
