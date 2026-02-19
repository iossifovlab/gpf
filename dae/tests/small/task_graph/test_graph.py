# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pytest
from dae.task_graph.graph import TaskGraph, chain_tasks


def test_creating_two_tasks_with_the_same_id() -> None:
    graph = TaskGraph()
    graph.create_task("ID", lambda: None, args=[], deps=[])
    with pytest.raises(ValueError):  # noqa
        graph.create_task("ID", lambda: None, args=[], deps=[])


def task_a_fn() -> str:
    return "result A"


def task_b_fn(a: str) -> str:
    return f"result B with {a}"


def test_chain_tasks() -> None:
    graph = TaskGraph()
    task_a = graph.make_task(
        "A", task_a_fn, args=[], deps=[])
    task_b = graph.make_task(
        "B", task_b_fn, args=[task_a.task], deps=[task_a.task])

    task = chain_tasks(task_a, task_b)
    assert task is not None

    res = task.func(*task.args, **task.kwargs)
    assert res == "result B with result A"
