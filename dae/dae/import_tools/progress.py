from abc import abstractmethod
from typing import cast
import fsspec

from dae.import_tools.task_graph import TaskGraph, TaskNode
from dae.utils import fs_utils


class Progress:
    """Determine if a task in a task graph need to run again or not."""

    @abstractmethod
    def set_task_graph(self, graph: TaskGraph):
        """Set the task graph for which we want to determine progress."""

    @abstractmethod
    def needs_to_run(self, task_node: TaskNode) -> bool:
        """Return true if the task needs to be rerun."""

    @abstractmethod
    def finished(self, task_node: TaskNode):
        """Call when a task has finished executing."""


class AlwaysRunProgress(Progress):
    """Don't check any conditions and just run any task."""

    def set_task_graph(self, graph: TaskGraph):
        pass

    def needs_to_run(self, task_node: TaskNode) -> bool:
        return True

    def finished(self, task_node: TaskNode) -> bool:
        pass


class FileProgress(Progress):
    """Use file modification timestamps to determine if a task needs to run."""

    def __init__(self, flag_dir="flags/"):
        self.flag_dir = flag_dir
        self._global_dependancies: list[str] = []

    def set_task_graph(self, graph: TaskGraph):
        self._check_ids_are_unique(graph)
        self._global_dependancies = graph.input_files

    def needs_to_run(self, task_node: TaskNode) -> bool:
        input_files = task_node.input_files + self._global_dependancies
        for dep in task_node.deps:
            input_files.append(self._get_flag_filename(dep))
        output_file = self._get_flag_filename(task_node)
        return self._are_files_newer_than(input_files, [output_file])

    def finished(self, task_node: TaskNode):
        with fsspec.open(self._get_flag_filename(task_node), "w"):
            pass

    def _check_ids_are_unique(self, graph):
        seen = set()
        for node in graph.nodes:
            node_id = self._get_id(node)
            if node_id in seen:
                raise ValueError(
                    f"The task graph has two nodes with the same id {node_id}"
                )
            seen.add(node_id)

    @staticmethod
    def _get_id(task_node):
        non_task_args = [
            arg for arg in task_node.args if not isinstance(arg, TaskNode)
        ]
        args_str = ",".join(str(arg) for arg in non_task_args)
        return f"{task_node.name}({args_str})"

    def _get_flag_filename(self, task_node):
        return fs_utils.join(self.flag_dir, self._get_id(task_node) + ".flag")

    def _are_files_newer_than(self, input_files, output_files) -> bool:
        input_mtime = self._get_last_mod_time(input_files)
        output_mtime = self._get_last_mod_time(output_files)
        if input_mtime is None or output_mtime is None:
            return True  # cannot determine mod times. Always run.
        return cast(bool, input_mtime >= output_mtime)

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
        try:
            return fs_utils.modified(path)
        except Exception:  # pylint: disable=broad-except
            return None
