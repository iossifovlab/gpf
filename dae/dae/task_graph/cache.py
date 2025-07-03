from __future__ import annotations

import datetime
import logging
import os
import pickle  # noqa: S403
from abc import abstractmethod
from collections.abc import Generator, Iterator
from copy import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

import fsspec

from dae.task_graph.graph import Task, TaskGraph
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


class CacheRecordType(Enum):
    NEEDS_COMPUTE = 0
    COMPUTED = 1
    ERROR = 2


@dataclass(frozen=True)
class CacheRecord:
    """Encapsulate information about a task in the cache."""

    type: CacheRecordType
    result_or_error: Any = None

    @property
    def result(self) -> Any:
        assert self.type == CacheRecordType.COMPUTED
        return self.result_or_error

    @property
    def error(self) -> Any:
        assert self.type == CacheRecordType.ERROR
        return self.result_or_error


class TaskCache:
    """Store the result of a task in a file and reuse it if possible."""

    @abstractmethod
    def load(self, graph: TaskGraph) -> Iterator[tuple[Task, CacheRecord]]:
        """For task in the `graph` load and yield the cache record."""

    @abstractmethod
    def cache(
        self, task_node: Task, *,
        is_error: bool, result: Any,
    ) -> None:
        """Cache the result or exception of a task."""

    @staticmethod
    def create(
        *,
        force: bool = False,
        task_progress_mode: bool = True,
        cache_dir: str | None = None,
    ) -> TaskCache:
        """Create the appropriate task cache."""
        if not task_progress_mode:
            return NoTaskCache()
        if cache_dir is None:
            cache_dir = os.getcwd()
        return FileTaskCache(force=force, cache_dir=cache_dir)


class NoTaskCache(dict, TaskCache):
    """Don't check any conditions and just run any task."""

    def load(
        self, graph: TaskGraph,
    ) -> Generator[tuple[Task, CacheRecord], None, None]:
        for task in graph.tasks:
            yield task, CacheRecord(CacheRecordType.NEEDS_COMPUTE)

    def cache(
        self, task_node: Task, *,
        is_error: bool, result: Any,
    ) -> None:
        pass


class FileTaskCache(TaskCache):
    """Use file modification timestamps to determine if a task needs to run."""

    def __init__(self, cache_dir: str, *, force: bool = False):
        self.force = force
        self.cache_dir = cache_dir
        self._global_dependancies: list[str] | None = None
        self._mtime_cache: dict[str, datetime.datetime] = {}

    def load(
        self, graph: TaskGraph,
    ) -> Generator[tuple[Task, CacheRecord], None, None]:
        assert self._global_dependancies is None
        self._global_dependancies = graph.input_files
        task2record: dict[Task, CacheRecord] = {}
        for task in graph.tasks:
            yield task, self._get_record(task, task2record)
        self._global_dependancies = None
        self._mtime_cache = {}

    def _get_record(
            self, task_node: Task, task2record: dict[Task, CacheRecord],
    ) -> CacheRecord:
        if self.force:
            return CacheRecord(CacheRecordType.NEEDS_COMPUTE)

        record = task2record.get(task_node)
        if record is not None:
            return record

        unsatisfied_deps = False
        for dep in task_node.deps:
            dep_rec = self._get_record(dep, task2record)
            if dep_rec.type != CacheRecordType.COMPUTED:
                unsatisfied_deps = True
                break

        if unsatisfied_deps or self._needs_compute(task_node):
            res_record = CacheRecord(CacheRecordType.NEEDS_COMPUTE)
            task2record[task_node] = res_record
            return res_record

        output_fn = self._get_flag_filename(task_node)
        with fsspec.open(output_fn, "rb") as cache_file:
            res_record = cast(
                CacheRecord,
                pickle.load(cache_file))  # pyright: ignore
            task2record[task_node] = res_record
            return res_record

    def _needs_compute(self, task: Task) -> bool:
        # check _global_dependancies only for first level task_nodes
        if len(task.deps) == 0:
            in_files = copy(self._global_dependancies)
        else:
            in_files = []
        assert in_files is not None
        in_files.extend(task.input_files)
        for dep in task.deps:
            in_files.append(self._get_flag_filename(dep))

        output_fn = self._get_flag_filename(task)
        return self._should_recompute_output(in_files, [output_fn])

    def cache(self, task_node: Task, *, is_error: bool, result: Any) -> None:
        record_type = (
            CacheRecordType.ERROR if is_error else CacheRecordType.COMPUTED
        )
        record = CacheRecord(
            record_type,
            result,
        )
        cache_fn = self._get_flag_filename(task_node)
        try:
            with fsspec.open(cache_fn, "wb") as cache_file:
                pickle.dump(record, cache_file)  # pyright: ignore
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Cannot write cache for task %s. Ignoring and continuing.",
                task_node,
            )

    def _get_flag_filename(self, task_node: Task) -> str:
        return fs_utils.join(self.cache_dir, f"{task_node.task_id}.flag")

    def _should_recompute_output(
        self, input_files: list[str], output_files: list[str],
    ) -> bool:
        input_mtime = self._get_last_mod_time(input_files)
        output_mtime = self._get_last_mod_time(output_files)
        if len(input_files) == 0 and output_mtime is not None:
            return False  # No input, but output file exists, don't recompute
        if input_mtime is None or output_mtime is None:
            return True  # cannot determine mod times. Always run.
        should_run: bool = input_mtime > output_mtime
        return should_run

    def _get_last_mod_time(
        self, filenames: list[str],
    ) -> datetime.datetime | None:
        mtimes = [self._safe_getmtime(path) for path in filenames]
        if any(p is None for p in mtimes):
            # cannot determine the mtime of a filename. Assume it needs recalc.
            return None
        if len(mtimes) > 0:
            return max(cast(list[datetime.datetime], mtimes))
        return None

    def _safe_getmtime(self, path: str) -> datetime.datetime | None:
        assert self._mtime_cache is not None
        if path in self._mtime_cache:
            return self._mtime_cache[path]
        if fs_utils.exists(path):
            mtime = fs_utils.modified(path)
            self._mtime_cache[path] = mtime
            return mtime
        return None
