# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613,protected-access
import os
import pickle  # noqa: S403
import time
from collections.abc import Generator
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from gain.task_graph.cache import CacheRecord, CacheRecordType, FileTaskCache
from gain.task_graph.graph import Task, TaskGraph, _Task
from gain.task_graph.sequential_executor import SequentialExecutor


def noop(*args: Any, **kwargs: Any) -> None:
    pass


@pytest.fixture
def graph() -> TaskGraph:
    graph = TaskGraph()
    first_task = graph.create_task("First", noop, args=[], deps=[])
    second_layer_tasks = [
        graph.create_task(f"Second {i}", noop, args=[], deps=[first_task])
        for i in range(10)
    ]
    intermediate_task = graph.create_task(
        "Intermediate", noop,
        args=[], deps=second_layer_tasks[-1:],  # just the last one
    )
    third_task = graph.create_task(
        "Third", noop, args=[],
        deps=[*second_layer_tasks, intermediate_task],
    )
    graph.create_task("Fourth", noop, args=[], deps=[third_task])
    return graph


def execute_with_file_cache(graph: TaskGraph, work_dir: str) -> None:
    executor = SequentialExecutor(FileTaskCache(cache_dir=work_dir))
    for _ in executor.execute(graph):
        pass


def test_graph(graph: TaskGraph) -> None:
    assert len(graph.tasks) == 14
    executor = SequentialExecutor()
    result = list(executor.execute(graph))
    assert len(result) == 14


def test_get_record_force_returns_needs_compute(tmp_path: Path) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    graph = TaskGraph()
    task = graph.create_task("Task", noop, args=[], deps=[])
    with graph:
        record = cache.get_record(graph.get_task_desc(task))

    assert record.type == CacheRecordType.NEEDS_COMPUTE


def test_get_record_returns_cached_entry(tmp_path: Path) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    graph = TaskGraph()
    task = graph.create_task("Task", noop, args=[], deps=[])
    cached = CacheRecord(CacheRecordType.COMPUTED, "cached")
    cache.cache(task, is_error=False, result=cached.result_or_error)
    with graph:
        record = cache.get_record(graph.get_task_desc(task))

    assert record == cached


def test_get_record_reads_serialized_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))

    graph = TaskGraph()
    task = graph.create_task("task", noop, args=[], deps=[])

    flag_path = tmp_path / "task.flag"
    monkeypatch.setattr(
        cache, "_get_flag_filename", lambda _task: str(flag_path),
    )

    expected = CacheRecord(CacheRecordType.COMPUTED, "payload")
    with open(flag_path, "wb") as out:
        pickle.dump(expected, out)

    with graph as graph_tasks:
        task_node = graph_tasks[task]
        result = cache.get_record(graph.get_task_desc(task_node.task))

    assert result == expected


def test_file_cache_clear_state(
        graph: TaskGraph, tmp_path: Path) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    for task in graph.tasks:
        assert cache.get_record(
            graph.get_task_desc(task)).type == CacheRecordType.NEEDS_COMPUTE


def test_file_cache_just_executed(graph: TaskGraph, tmp_path: Path) -> None:
    working_graph = deepcopy(graph)

    executor = SequentialExecutor(FileTaskCache(cache_dir=str(tmp_path)))
    result = list(executor.execute(working_graph))

    assert len(result) == len(graph.tasks)

    cache = FileTaskCache(cache_dir=str(tmp_path))
    for task in graph.tasks:
        assert cache.get_record(
            graph.get_task_desc(task),
        ).type == CacheRecordType.COMPUTED


def test_file_cache_touch_input_file(graph: TaskGraph, tmp_path: Path) -> None:
    config_fn = str(tmp_path / "config.yaml")
    touch(config_fn)
    graph.input_files.append(config_fn)

    executor = SequentialExecutor(FileTaskCache(cache_dir=str(tmp_path)))
    for _ in executor.execute(graph):
        pass

    touch(config_fn)
    cache = FileTaskCache(cache_dir=str(tmp_path))
    for task in graph.tasks:
        assert cache.get_record(
            graph.get_task_desc(task),
        ).type == CacheRecordType.NEEDS_COMPUTE


@pytest.mark.parametrize("operation", ["touch", "remove"])
def test_file_cache_mod_input_file_of_intermediate_node(
    graph: TaskGraph, tmp_path: Path, operation: str,
) -> None:
    dep_fn = str(tmp_path / "file-used-by-intermediate-node")
    touch(dep_fn)
    with graph as graph_tasks:
        int_node = graph_tasks[Task("Intermediate")]

    assert int_node is not None
    int_node.input_files.append(dep_fn)

    working_graph = deepcopy(graph)
    execute_with_file_cache(working_graph, str(tmp_path))

    if operation == "touch":
        touch(dep_fn)
    else:
        assert operation == "remove"
        os.remove(dep_fn)
    cache = FileTaskCache(cache_dir=str(tmp_path))
    int_record = cache.get_record(graph.get_task_desc(int_node.task))

    assert int_record.type == CacheRecordType.NEEDS_COMPUTE
    for task in _get_task_descendants(graph, int_node):
        assert cache.get_record(
            graph.get_task_desc(task.task),
        ).type == CacheRecordType.NEEDS_COMPUTE


@pytest.mark.parametrize("operation", ["touch", "remove"])
def test_file_cache_mod_flag_file_of_intermediate_node(
    graph: TaskGraph, tmp_path: Path, operation: str,
) -> None:
    working_graph = deepcopy(graph)
    execute_with_file_cache(working_graph, str(tmp_path))

    cache = FileTaskCache(cache_dir=str(tmp_path))
    with graph as graph_tasks:
        for task in graph_tasks.values():
            record = cache.get_record(graph.get_task_desc(task.task))
            assert record.type == CacheRecordType.COMPUTED

    with graph as graph_tasks:
        first_task = graph_tasks[Task("First")]
    assert first_task is not None

    if operation == "touch":
        touch(cache._get_flag_filename(first_task.task))
        first_task_record = cache.get_record(
            graph.get_task_desc(first_task.task))
        assert first_task_record.type == CacheRecordType.COMPUTED
    else:
        assert operation == "remove"
        os.remove(cache._get_flag_filename(first_task.task))
        first_task_record = cache.get_record(
            graph.get_task_desc(first_task.task))
        assert first_task_record.type == CacheRecordType.NEEDS_COMPUTE

    for task in _get_task_descendants(graph, first_task):
        record = cache.get_record(graph.get_task_desc(task.task))
        assert record.type == CacheRecordType.NEEDS_COMPUTE


def test_file_cache_very_large_task_name(tmp_path: Path) -> None:
    graph = TaskGraph()
    graph.create_task("Task" * 500, noop, args=[], deps=[])

    executor = SequentialExecutor(FileTaskCache(cache_dir=str(tmp_path)))
    for _ in executor.execute(graph):
        pass


def touch(filename: str) -> None:
    if os.path.exists(filename):
        # fsspec local file system has a resolution of 1 second so we have to
        # wait in order to make sure that the mtime will get updated
        time.sleep(1)
    Path(filename).touch()


def _get_task_by_id(graph: TaskGraph, task_id: str) -> Task | None:
    for task in graph.tasks:
        if task.task_id == task_id:
            return task
    return None


def _get_task_descendants(
    graph: TaskGraph, parent_task: _Task,
) -> Generator[_Task, None, None]:
    with graph as graph_tasks:
        for task in graph_tasks.values():
            if _is_task_descendant(graph_tasks, task, parent_task):
                yield task


def _is_task_descendant(
    graph_tasks: dict[Task, _Task],
    child_task: _Task, parent_task: _Task,
) -> bool:
    if parent_task in child_task.deps:
        return True
    return any(
        _is_task_descendant(
            graph_tasks,
            graph_tasks[dep], parent_task)
        for dep in child_task.deps
    )
