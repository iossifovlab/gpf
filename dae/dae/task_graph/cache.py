from abc import abstractmethod
from copy import copy
from dataclasses import dataclass
from enum import Enum
import pickle
from typing import Any, cast
import fsspec

from dae.task_graph.graph import TaskGraph, Task
from dae.utils import fs_utils


class CacheRecordType(Enum):
    MISSING = 0
    COMPUTED = 1
    ERROR = 2


@dataclass(frozen=True)
class CacheRecord:
    """Encapsulate information about a task in the cache."""

    type: CacheRecordType
    result_or_exception: Any = None

    @property
    def result(self):
        assert self.type == CacheRecordType.COMPUTED
        return self.result_or_exception

    @property
    def error(self):
        assert self.type == CacheRecordType.ERROR
        return self.result_or_exception


class TaskCache:
    """Store the result of a task in a file and reuse it if possible."""

    @abstractmethod
    def prepare(self, graph: TaskGraph):
        """Prepare the cache for quering for the specific graph."""

    @abstractmethod
    def get_record(self, task_node: Task) -> CacheRecord:
        """Return a record describing the kind of cache entry for the task."""

    @abstractmethod
    def cache(self, task_node: Task, is_error: bool, result: Any):
        """Cache the result or excpetion of a task."""


class NoTaskCache(dict, TaskCache):
    """Don't check any conditions and just run any task."""

    def prepare(self, graph: TaskGraph):
        pass

    def get_record(self, task_node: Task) -> CacheRecord:
        return CacheRecord(CacheRecordType.MISSING)

    def cache(self, task_node: Task, is_error: bool, result: Any):
        pass


class FileTaskCache(TaskCache):
    """Use file modification timestamps to determine if a task needs to run."""

    def __init__(self, force=False, work_dir=None):
        self.force = force
        self.cache_dir = fs_utils.join(work_dir or "", ".task-progress/")
        self._global_dependancies: list[str] = []

    def prepare(self, graph: TaskGraph):
        self._global_dependancies = graph.input_files

    def get_record(self, task_node: Task) -> CacheRecord:
        if self.force:
            return CacheRecord(CacheRecordType.MISSING)

        if self._needs_compute(task_node):
            return CacheRecord(CacheRecordType.MISSING)

        output_fn = self._get_flag_filename(task_node)
        with fsspec.open(output_fn, "rb") as cache_file:
            return cast(CacheRecord, pickle.load(cache_file))

    def _needs_compute(self, task):
        in_files = copy(self._global_dependancies)
        self._add_dep_files(task, in_files)
        output_fn = self._get_flag_filename(task)
        return self._should_recompute_output(in_files, [output_fn])

    def _add_dep_files(self, task, files):
        files.extend(task.input_files)
        for dep in task.deps:
            files.append(self._get_flag_filename(dep))
            self._add_dep_files(dep, files)

    def cache(self, task_node: Task, is_error: bool, result: Any):
        cache_fn = self._get_flag_filename(task_node)
        with fsspec.open(cache_fn, "wb") as cache_file:
            record_type = (
                CacheRecordType.ERROR if is_error else CacheRecordType.COMPUTED
            )
            record = CacheRecord(
                record_type,
                result
            )
            pickle.dump(record, cache_file)

    def _get_flag_filename(self, task_node):
        return fs_utils.join(self.cache_dir, f"{task_node.task_id}.flag")

    def _should_recompute_output(self, input_files, output_files) -> bool:
        input_mtime = self._get_last_mod_time(input_files)
        output_mtime = self._get_last_mod_time(output_files)
        if len(input_files) == 0 and output_mtime is not None:
            return False  # No input, but output file exists, don't recompute
        if input_mtime is None or output_mtime is None:
            return True  # cannot determine mod times. Always run.
        should_run: bool = input_mtime > output_mtime
        return should_run

    def _get_last_mod_time(self, filenames: list[str]):
        mtimes = [self._safe_getmtime(path) for path in filenames]
        if any(p is None for p in mtimes):
            # cannot determine the mtime of a filename. Assume it needs recalc.
            return None
        if len(mtimes) > 0:
            return max(mtimes)
        return None

    @staticmethod
    def _safe_getmtime(path):
        if fs_utils.exists(path):
            return fs_utils.modified(path)
        return None
