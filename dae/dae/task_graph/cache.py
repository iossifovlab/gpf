from __future__ import annotations

import datetime
import logging
import os
import pickle  # noqa: S403
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

import fsspec

from dae.task_graph.graph import Task, TaskDesc
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

    def invalidate(self) -> CacheRecord:
        """Return a new instance that needs to be recomputed."""
        return CacheRecord(CacheRecordType.NEEDS_COMPUTE, self.result_or_error)


class TaskCache:
    """Store the result of a task in a file and reuse it if possible."""

    @abstractmethod
    def get_record(
        self, task_desc: TaskDesc,
    ) -> CacheRecord:
        """For task in the `graph` load and yield the cache record."""

    @abstractmethod
    def cache(
        self, task: Task, *,
        is_error: bool, result: Any,
    ) -> None:
        """Cache the result or exception of a task."""

    @staticmethod
    def create(
        *,
        task_progress_mode: bool = True,
        cache_dir: str | None = None,
    ) -> TaskCache:
        """Create the appropriate task cache."""
        if not task_progress_mode:
            return NoTaskCache()
        if cache_dir is None:
            cache_dir = os.getcwd()
        return FileTaskCache(cache_dir=cache_dir)


class NoTaskCache(dict, TaskCache):
    """Don't check any conditions and just run any task."""

    def get_record(
        self, task_desc: TaskDesc,  # noqa: ARG002
    ) -> CacheRecord:
        return CacheRecord(CacheRecordType.NEEDS_COMPUTE)

    def cache(
        self, task: Task, *,
        is_error: bool, result: Any,
    ) -> None:
        pass


class FileTaskCache(TaskCache):
    """Use file modification timestamps to determine if a task needs to run."""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir

    def get_record(self, task_desc: TaskDesc) -> CacheRecord:
        """Get the cache record for a task."""
        flag_filename = self._get_flag_filename(task_desc.task)
        with fsspec.open(flag_filename, "rb") as cache_file:
            try:
                task_record = cast(
                    CacheRecord,
                    pickle.load(cache_file))  # pyright: ignore
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    "Cannot read status for task %s. Ignoring and continuing.",
                    task_desc,
                )
                return CacheRecord(CacheRecordType.NEEDS_COMPUTE)

        if task_record.type != CacheRecordType.COMPUTED:
            return task_record

        if self._needs_recompute(task_desc):
            task_record = CacheRecord(
                CacheRecordType.NEEDS_COMPUTE,
                result_or_error=task_record.result,
            )

        return task_record

    def cache(self, task: Task, *, is_error: bool, result: Any) -> None:
        record_type = (
            CacheRecordType.ERROR if is_error else CacheRecordType.COMPUTED
        )
        record = CacheRecord(
            record_type,
            result,
        )
        cache_fn = self._get_flag_filename(task)
        try:
            with fsspec.open(cache_fn, "wb") as cache_file:
                pickle.dump(record, cache_file)  # pyright: ignore
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Cannot write cache for task %s. Ignoring and continuing.",
                task,
            )

    def _get_flag_filename(self, task: Task) -> str:
        return fs_utils.join(self.cache_dir, f"{task.task_id}.flag")

    def _needs_recompute(
        self, task: TaskDesc,
    ) -> bool:
        """
        Determine if a task needs to be recomputed.

        A task needs to be recomputed if the newest input_file is newer than
        the newest output file. If any of the output files do not exist,
        the task will also need to be recomputed.
        """
        input_files = task.input_files
        output_files = [self._get_flag_filename(task.task), *task.output_files]
        input_mtime = self._get_newest_mod_time(input_files)
        output_mtime = self._get_oldest_mod_time(output_files)
        if len(input_files) == 0 and output_mtime is not None:
            return False  # No input, but output file exists, don't recompute
        if input_mtime is None or output_mtime is None:
            return True  # cannot determine mod times. Always run.
        should_run: bool = input_mtime > output_mtime
        return should_run

    def _get_oldest_mod_time(
        self, filenames: list[str],
    ) -> datetime.datetime | None:
        mtimes = [self._safe_getmtime(path) for path in filenames]
        if any(p is None for p in mtimes):
            # cannot determine the mtime of a filename. Assume it needs recalc.
            return None
        if len(mtimes) > 0:
            return min(cast(list[datetime.datetime], mtimes))
        return None

    def _get_newest_mod_time(
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
        if fs_utils.exists(path):
            return fs_utils.modified(path)
        return None
