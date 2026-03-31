# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pytest
from gain.task_graph.executor import TaskGraphExecutor
from gain.task_graph.graph import TaskDesc, TaskGraph, chain_tasks


def test_creating_two_tasks_with_the_same_id() -> None:
    graph = TaskGraph()
    graph.create_task("ID", lambda: None, args=[], deps=[])
    with pytest.raises(ValueError):  # noqa
        graph.create_task("ID", lambda: None, args=[], deps=[])


def task_a_fn() -> str:
    return "result A"


def task_b_fn(a: str) -> str:
    return f"result B with ({a})"


def task_c_fn(b: str) -> str:
    return f"result C with ({b})"


def task_d_fn() -> str:
    return "result D"


task_a = TaskGraph.make_task(
    "A", task_a_fn, args=[], deps=[])
task_b = TaskGraph.make_task(
    "B", task_b_fn, args=[task_a.task], deps=[task_a.task])
task_c = TaskGraph.make_task(
    "C", task_c_fn, args=[task_b.task], deps=[task_b.task])
task_d = TaskGraph.make_task(
    "D", task_d_fn, args=[], deps=[])


@pytest.mark.parametrize(
    "tasks, expected", [
        ([task_a, task_d], "result D"),
        ([task_a, task_b], "result B with (result A)"),
        ([task_a, task_b, task_c], "result C with (result B with (result A))"),
        ([task_a, task_b, task_c, task_d], "result D"),
        ([task_a, task_b, task_d], "result D"),
        ([task_d, task_a, task_b, task_c],
         "result C with (result B with (result A))"),
    ],
)
def test_chain_tasks(
    tasks: list[TaskDesc],
    expected: str,
) -> None:

    task = chain_tasks(*tasks)
    assert task is not None

    res = task.func(*task.args, **task.kwargs)
    assert res == expected


@pytest.mark.parametrize(
    "tasks, task_id, expected", [
        ([task_a, task_d], "D", "result D"),
        ([task_a, task_b],
         "B", "result B with (result A)"),
        ([task_a, task_b, task_c],
         "C", "result C with (result B with (result A))"),
        ([task_a, task_b, task_c, task_d],
         "D", "result D"),
        ([task_d, task_a, task_b, task_c],
         "C", "result C with (result B with (result A))"),
    ],
)
def test_executor_chain_tasks(
    executor: TaskGraphExecutor,
    tasks: list[TaskDesc],
    task_id: str,
    expected: str,
) -> None:
    graph = TaskGraph()

    task = chain_tasks(*tasks)
    graph.add_task(task)

    executed_tasks = list(executor.execute(graph))
    assert len(executed_tasks) == 1
    ex_task, ex_res = executed_tasks[0]
    assert ex_task.task_id == task_id
    assert ex_res == expected
