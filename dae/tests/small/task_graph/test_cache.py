# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613,protected-access
import os
import pickle  # noqa: S403
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from dae.task_graph.cache import CacheRecord, CacheRecordType, FileTaskCache
from dae.task_graph.graph import Task, TaskGraph
from dae.task_graph.sequential_executor import SequentialExecutor


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


def test_get_record_force_returns_needs_compute(tmp_path: Path) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path), force=True)
    task = TaskGraph().create_task("Task", noop, args=[], deps=[])

    record = cache._get_record(task, {})

    assert record.type == CacheRecordType.NEEDS_COMPUTE


def test_get_record_returns_cached_entry(tmp_path: Path) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    task = TaskGraph().create_task("Task", noop, args=[], deps=[])
    cached = CacheRecord(CacheRecordType.COMPUTED, "cached")
    task2record = {task: cached}

    record = cache._get_record(task, task2record)

    assert record is cached


def test_get_record_requires_compute_if_deps_not_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    cache._global_dependancies = []
    monkeypatch.setattr(cache, "_needs_compute", lambda _task: False)

    graph = TaskGraph()
    dep = graph.create_task("dep", noop, args=[], deps=[])
    task = graph.create_task("task", noop, args=[], deps=[dep])
    task2record = {dep: CacheRecord(CacheRecordType.NEEDS_COMPUTE)}

    record = cache._get_record(task, task2record)

    assert record.type == CacheRecordType.NEEDS_COMPUTE
    assert task2record[task] is record


def test_get_record_reads_serialized_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    cache._global_dependancies = []
    monkeypatch.setattr(cache, "_needs_compute", lambda _task: False)

    graph = TaskGraph()
    task = graph.create_task("task", noop, args=[], deps=[])

    flag_path = tmp_path / "task.flag"
    monkeypatch.setattr(
        cache, "_get_flag_filename", lambda _task: str(flag_path),
    )

    expected = CacheRecord(CacheRecordType.COMPUTED, "payload")
    with open(flag_path, "wb") as out:
        pickle.dump(expected, out)

    task2record: dict[Task, CacheRecord] = {}
    result = cache._get_record(task, task2record)

    assert result == expected
    assert task2record[task] == expected


def test_file_cache_clear_state(
        graph: TaskGraph, tmp_path: Path) -> None:
    cache = FileTaskCache(cache_dir=str(tmp_path))
    task2record = dict(cache.load(graph))
    for task in graph.tasks:
        assert task2record[task].type == CacheRecordType.NEEDS_COMPUTE


def test_file_cache_just_executed(graph: TaskGraph, tmp_path: Path) -> None:
    executor = SequentialExecutor(FileTaskCache(cache_dir=str(tmp_path)))
    for _ in executor.execute(graph):
        pass

    cache = FileTaskCache(cache_dir=str(tmp_path))
    task2record = dict(cache.load(graph))
    for task in graph.tasks:
        assert task2record[task].type == CacheRecordType.COMPUTED


def test_file_cache_touch_input_file(graph: TaskGraph, tmp_path: Path) -> None:
    config_fn = str(tmp_path / "config.yaml")
    touch(config_fn)
    graph.input_files.append(config_fn)

    executor = SequentialExecutor(FileTaskCache(cache_dir=str(tmp_path)))
    for _ in executor.execute(graph):
        pass

    touch(config_fn)
    cache = FileTaskCache(cache_dir=str(tmp_path))
    task2record = dict(cache.load(graph))
    for task in graph.tasks:
        assert task2record[task].type == CacheRecordType.NEEDS_COMPUTE


@pytest.mark.parametrize("operation", ["touch", "remove"])
def test_file_cache_mod_input_file_of_intermediate_node(
    graph: TaskGraph, tmp_path: Path, operation: str,
) -> None:
    dep_fn = str(tmp_path / "file-used-by-intermediate-node")
    touch(dep_fn)
    int_node = get_task_by_id(graph, "Intermediate")
    assert int_node is not None
    int_node.input_files.append(dep_fn)

    execute_with_file_cache(graph, str(tmp_path))

    if operation == "touch":
        touch(dep_fn)
    else:
        assert operation == "remove"
        os.remove(dep_fn)
    cache = FileTaskCache(cache_dir=str(tmp_path))
    task2record = dict(cache.load(graph))

    assert task2record[int_node].type == CacheRecordType.NEEDS_COMPUTE
    for task in get_task_descendants(graph, int_node):
        assert task2record[task].type == CacheRecordType.NEEDS_COMPUTE


@pytest.mark.parametrize("operation", ["touch", "remove"])
def test_file_cache_mod_flag_file_of_intermediate_node(
    graph: TaskGraph, tmp_path: Path, operation: str,
) -> None:
    execute_with_file_cache(graph, str(tmp_path))

    cache = FileTaskCache(cache_dir=str(tmp_path))
    task2record = dict(cache.load(graph))
    for record in task2record.values():
        assert record.type == CacheRecordType.COMPUTED

    first_task = get_task_by_id(graph, "First")
    assert first_task is not None

    if operation == "touch":
        touch(cache._get_flag_filename(first_task))
        task2record = dict(cache.load(graph))
        assert task2record[first_task].type == CacheRecordType.COMPUTED
    else:
        assert operation == "remove"
        os.remove(cache._get_flag_filename(first_task))
        task2record = dict(cache.load(graph))
        assert task2record[first_task].type == CacheRecordType.NEEDS_COMPUTE

    for task in get_task_descendants(graph, first_task):
        assert task2record[task].type == CacheRecordType.NEEDS_COMPUTE


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


def get_task_by_id(graph: TaskGraph, task_id: str) -> Task | None:
    for task in graph.tasks:
        if task.task_id == task_id:
            return task
    return None


def get_task_descendants(
    graph: TaskGraph, parent_task: Task,
) -> Generator[Task, None, None]:
    for task in graph.tasks:
        if is_task_descendant(task, parent_task):
            yield task


def is_task_descendant(child_task: Task, parent_task: Task) -> bool:
    if parent_task in child_task.deps:
        return True
    return any(
        is_task_descendant(dep, parent_task) for dep in child_task.deps
    )
