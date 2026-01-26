# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pytest
from dae.task_graph.graph import TaskGraph


@pytest.mark.parametrize(
    "tasks,expected_order", [
        (  # simple chain
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["B"]),
            ],
            ["A", "B", "C"],
        ),
        (  # diamond
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B", "C"]),
            ],
            ["A", "B", "C", "D"],
        ),
        (  # wide graph
            [
                ("A", []),
                ("B", []),
                ("C", []),
                ("D", []),
                ("E", ["A", "B", "C", "D"]),
            ],
            ["A", "B", "C", "D", "E"],
        ),
        (  # complex graph
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["B", "C"]),
                ("F", ["D", "E"]),
            ],
            ["A", "B", "C", "D", "E", "F"],
        ),
        (
            [  # multiple roots
                ("A", []),
                ("B", []),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["C", "D"]),
            ],
            ["A", "B", "C", "D", "E"],
        ),
        (
            [  # multiple independent chains
                ("A1", []),
                ("B1", ["A1"]),
                ("C1", ["B1"]),
                ("A2", []),
                ("B2", ["A2"]),
                ("C2", ["B2"]),
            ],
            ["A1", "A2", "B1", "B2", "C1", "C2"],
        ),
        (
            [
                ("3", []),
                ("2", []),
                ("1", ["2", "3"]),
            ],
            ["2", "3", "1"],
        ),
    ],
)
def test_graph_order(
    tasks: list[tuple[str, list[str]]],
    expected_order: list[str],
) -> None:
    graph = TaskGraph()
    for task_id, dep_ids in tasks:
        deps = [graph.get_task(dep_id) for dep_id in dep_ids]
        graph.create_task(task_id, lambda: None, args=[], deps=deps)

    tasks_in_order = graph.topological_order()
    ids_in_order = [task.task_id for task in tasks_in_order]

    assert ids_in_order == expected_order


@pytest.mark.parametrize(
    "tasks,ready_seq", [
        (  # 0: simple chain
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["B"]),
            ],
            [["A"], ["B"], ["C"]],
        ),
        (  # 1: diamond
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B", "C"]),
            ],
            [["A"], ["B", "C"], ["D"]],
        ),
        (  # 2: wide graph
            [
                ("A", []),
                ("B", []),
                ("C", []),
                ("D", []),
                ("E", ["A", "B", "C", "D"]),
            ],
            [["A", "B", "C", "D"], ["E"]],
        ),
        (  # 3: complex graph
            [
                ("A", []),
                ("B", ["A"]),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["B", "C"]),
                ("F", ["D", "E"]),
            ],
            [["A"], ["B", "C"], ["D", "E"], ["F"]],
        ),
        (
            [  # 4: multiple roots
                ("A", []),
                ("B", []),
                ("C", ["A"]),
                ("D", ["B"]),
                ("E", ["C", "D"]),
            ],
            [["A", "B"], ["C", "D"], ["E"]],
        ),
        (
            [  # 5: multiple independent chains
                ("A1", []),
                ("B1", ["A1"]),
                ("C1", ["B1"]),
                ("A2", []),
                ("B2", ["A2"]),
                ("C2", ["B2"]),
            ],
            [["A1", "A2"], ["B1", "B2"], ["C1", "C2"]],
        ),
        (
            [  # 6: simple graph with numeric ids
                ("3", []),
                ("2", []),
                ("1", ["2", "3"]),
            ],
            [["2", "3"], ["1"]],
        ),
    ],
)
def test_graph_ready_tasks(
    tasks: list[tuple[str, list[str]]],
    ready_seq: list[list[str]],
) -> None:
    graph = TaskGraph()
    for task_id, dep_ids in tasks:
        deps = [graph.get_task(dep_id) for dep_id in dep_ids]
        graph.create_task(task_id, lambda: None, args=[], deps=deps)

    for ready in ready_seq:
        ready_tasks = graph.ready_tasks()
        ids_in_order = {task.task_id for task in ready_tasks}
        assert ids_in_order == set(ready)
        graph.process_completed_tasks(
            [(task.task_id, "done") for task in ready_tasks])
