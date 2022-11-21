# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import os
from pathlib import Path
import time
import pytest

from dae.task_graph.executor import SequentialExecutor
from dae.task_graph.graph import TaskGraph
from dae.task_graph.cache import CacheRecordType, FileTaskCache


def noop(*args, **kwargs):
    pass


@pytest.fixture()
def graph():
    graph = TaskGraph()
    first_task = graph.create_task("First", noop, [], [])
    second_layer_tasks = [
        graph.create_task(f"Second {i}", noop, [], [first_task])
        for i in range(10)
    ]
    intermediate_task = graph.create_task(
        "Intermediate", noop, [], second_layer_tasks[-1:]  # just the last one
    )
    third_task = graph.create_task(
        "Third", noop, [], second_layer_tasks + [intermediate_task]
    )
    graph.create_task("Fourth", noop, [], [third_task])
    return graph


def execute_with_file_cache(graph, work_dir):
    executor = SequentialExecutor(FileTaskCache(work_dir=work_dir))
    for _ in executor.execute(graph):
        pass


def test_file_cache_clear_state(graph: TaskGraph, tmpdir):
    cache = FileTaskCache(work_dir=tmpdir)
    cache.set_task_graph(graph)
    for task in graph.tasks:
        assert cache.get_record(task).type == CacheRecordType.NEEDS_COMPUTE


def test_file_cache_just_executed(graph: TaskGraph, tmpdir):
    executor = SequentialExecutor(FileTaskCache(work_dir=tmpdir))
    for _ in executor.execute(graph):
        pass

    cache = FileTaskCache(work_dir=tmpdir)
    cache.set_task_graph(graph)
    for task in graph.tasks:
        assert cache.get_record(task).type == CacheRecordType.COMPUTED


def test_file_cache_touch_input_file(graph: TaskGraph, tmpdir):
    config_fn = str(tmpdir / "config.yaml")
    touch(config_fn)
    graph.input_files.append(config_fn)

    executor = SequentialExecutor(FileTaskCache(work_dir=tmpdir))
    for _ in executor.execute(graph):
        pass

    touch(config_fn)
    cache = FileTaskCache(work_dir=tmpdir)
    cache.set_task_graph(graph)
    for task in graph.tasks:
        assert cache.get_record(task).type == CacheRecordType.NEEDS_COMPUTE


@pytest.mark.parametrize("operation", ["touch", "remove"])
def test_file_cache_mod_input_file_of_intermediate_node(
    graph: TaskGraph, tmpdir, operation
):
    dep_fn = str(tmpdir / "file-used-by-intermediate-node")
    touch(dep_fn)
    int_node = get_task_by_id(graph, "Intermediate")
    int_node.input_files.append(dep_fn)

    execute_with_file_cache(graph, tmpdir)

    if operation == "touch":
        touch(dep_fn)
    else:
        assert operation == "remove"
        os.remove(dep_fn)
    cache = FileTaskCache(work_dir=tmpdir)
    cache.set_task_graph(graph)

    assert cache.get_record(int_node).type == CacheRecordType.NEEDS_COMPUTE
    for task in get_task_descendants(graph, int_node):
        assert cache.get_record(task).type == CacheRecordType.NEEDS_COMPUTE


@pytest.mark.parametrize("operation", ["touch", "remove"])
def test_file_cache_mod_flag_file_of_intermediate_node(
    graph: TaskGraph, tmpdir, operation
):
    execute_with_file_cache(graph, tmpdir)

    cache = FileTaskCache(work_dir=tmpdir)
    cache.set_task_graph(graph)
    first_task = get_task_by_id(graph, "First")
    if operation == "touch":
        touch(cache._get_flag_filename(first_task))
        assert cache.get_record(first_task).type == CacheRecordType.COMPUTED
    else:
        assert operation == "remove"
        os.remove(cache._get_flag_filename(first_task))
        assert cache.get_record(first_task).type == \
            CacheRecordType.NEEDS_COMPUTE

    for task in get_task_descendants(graph, first_task):
        assert cache.get_record(task).type == CacheRecordType.NEEDS_COMPUTE


def touch(filename):
    if os.path.exists(filename):
        # fsspec local file system has a resolution of 1 second so we have to
        # wait in order to make sure that the mtime will get updated
        time.sleep(1)
    Path(filename).touch()


def get_task_by_id(graph, task_id):
    for task in graph.tasks:
        if task.task_id == task_id:
            return task
    return None


def get_task_descendants(graph, parent_task):
    for task in graph.tasks:
        if is_task_descendant(task, parent_task):
            yield task


def is_task_descendant(child_task, parent_task):
    if parent_task in child_task.deps:
        return True
    for dep in child_task.deps:
        if is_task_descendant(dep, parent_task):
            return True
    return False
