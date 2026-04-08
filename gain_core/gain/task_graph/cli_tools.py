import argparse
import logging
import sys
import textwrap
import traceback
from collections.abc import Generator
from typing import Any

import yaml

from gain.task_graph.cache import CacheRecordType, NoTaskCache, TaskCache
from gain.task_graph.executor import (
    TaskGraphExecutor,
)
from gain.task_graph.graph import TaskGraph
from gain.task_graph.process_pool_executor import ProcessPoolTaskExecutor
from gain.task_graph.sequential_executor import SequentialExecutor

logger = logging.getLogger(__name__)


class TaskGraphCli:
    """Takes care of creating a task graph executor and executing a graph."""

    @staticmethod
    def add_arguments(
        parser: argparse.ArgumentParser, *,
        task_progress_mode: bool = True,
        default_task_status_dir: str | None = "./.task-progress",
        use_commands: bool = True,
    ) -> None:
        """Add arguments needed to execute a task graph."""
        executor_group = parser.add_argument_group(title="Task Graph Executor")
        # cluster_name
        # cluster_config_file
        executor_group.add_argument(
            "-j", "--jobs", type=int, default=None,
            help="Number of jobs to run in parallel. Defaults to the number "
            "of processors on the machine")

        executor_group.add_argument(
            "--process-pool", "--pp",
            dest="use_process_pool", action="store_true",
            help="Use a process pool executor with the specified number of "
            "processes instead of a dask distributed executor.",
        )
        executor_group.add_argument(
            "-N", "--dask-cluster-name", "--dcn",
            dest="dask_cluster_name",
            type=str, default=None,
            help="The named of the named dask cluster",
        )
        executor_group.add_argument(
            "-c", "--dccf", "--dask-cluster-config-file",
            dest="dask_cluster_config_file",
            type=str, default=None,
            help="dask cluster config file",
        )
        executor_group.add_argument(
            "--task-log-dir", dest="task_log_dir", type=str,
            default=None,
            help="Path to directory where to store tasks' logs",
        )
        # task_cache
        execution_mode_group = parser.add_argument_group(
            title="Execution Mode")
        if use_commands:
            execution_mode_group.add_argument(
                "command",
                choices=["run", "list", "status"],
                default="run", nargs="?",
                help=textwrap.dedent("""\
                    Command to execute on the import configuration.
                    run - runs the import process
                    list - lists the tasks to be executed but doesn't run them
                    status - synonym for list
                """),
            )
        execution_mode_group.add_argument(
            "-t", "--task-ids", dest="task_ids", type=str, nargs="+")
        execution_mode_group.add_argument(
            "--keep-going", default=False, action="store_true",
            help="Whether or not to keep executing in case of an error",
        )
        execution_mode_group.add_argument(
            "--fork-tasks", "--fork-task", "--fork",
            dest="fork_tasks", action="store_true",
            help="Whether to fork a new worker process for each task",
        )

        if task_progress_mode:
            execution_mode_group.add_argument(
                "--force", "-f", default=False, action="store_true",
                help="Ignore precomputed state and always rerun all tasks.",
            )
            execution_mode_group.add_argument(
                "-d", "--task-status-dir", "--tsd",
                default=default_task_status_dir,
                type=str, help="Directory to store the task progress.",
            )

        else:
            assert not task_progress_mode, \
                "task_progress_mode must be False if no cache is used"

    @staticmethod
    def _create_dask_executor(
        task_cache: TaskCache,
        **kwargs: Any,
    ) -> TaskGraphExecutor:
        """Create a task graph executor according to the args specified."""
        # pylint: disable=import-outside-toplevel
        from gain.dask.named_cluster import (
            setup_client,
            setup_client_from_config,
        )
        from gain.task_graph.dask_executor import DaskExecutor

        assert kwargs.get("dask_cluster_name") is None or \
            kwargs.get("dask_cluster_config_file") is None
        if kwargs.get("dask_cluster_config_file") is not None:
            dask_cluster_config_file = kwargs.get("dask_cluster_config_file")
            assert dask_cluster_config_file is not None
            with open(dask_cluster_config_file) as conf_file:
                dask_cluster_config = yaml.safe_load(conf_file)
            logger.info(
                "THE CLUSTER CONFIG IS: %s; loaded from: %s",
                dask_cluster_config,
                kwargs.get("dask_cluster_config_file"))
            client, _ = setup_client_from_config(
                dask_cluster_config,
                number_of_workers=kwargs.get("jobs"),
            )
        else:
            client, _ = setup_client(
                kwargs.get("dask_cluster_name"),
                number_of_workers=kwargs.get("jobs"))

        logger.info("Working with client: %s", client)
        return DaskExecutor(client, task_cache=task_cache, **kwargs)

    @staticmethod
    def create_executor(
        task_cache: TaskCache | None = None,
        **kwargs: Any,
    ) -> TaskGraphExecutor:
        """Create a task graph executor according to the args specified."""
        if task_cache is None:
            task_cache = NoTaskCache()

        if kwargs.get("jobs", 1) == 1:
            assert kwargs.get("dask_cluster_name") is None
            assert kwargs.get("dask_cluster_config_file") is None
            return SequentialExecutor(task_cache=task_cache, **kwargs)

        if kwargs.get("use_process_pool"):
            assert kwargs.get("dask_cluster_name") is None
            assert kwargs.get("dask_cluster_config_file") is None
            return ProcessPoolTaskExecutor(
                max_workers=kwargs.get("jobs"),
                task_cache=task_cache,
                **kwargs)

        return TaskGraphCli._create_dask_executor(
            task_cache=task_cache, **kwargs)

    @staticmethod
    def process_graph(
        task_graph: TaskGraph, *,
        task_progress_mode: bool = True,
        **kwargs: Any,
    ) -> bool:
        """Process task_graph in according with the arguments in args.

        Return true if the graph get's successfully processed.
        """
        if kwargs.get("task_ids") is not None:
            task_graph.prune(tasks_to_keep=kwargs["task_ids"])

        task_cache = TaskCache.create(
            task_progress_mode=task_progress_mode,
            cache_dir=kwargs.get("task_status_dir"),
        )

        if kwargs.get("command") is None or kwargs.get("command") == "run":
            with TaskGraphCli.create_executor(task_cache, **kwargs) as xtor:
                return task_graph_run(
                    task_graph, xtor,
                    keep_going=kwargs.get("keep_going", False))

        if kwargs.get("command") in {"list", "status"}:
            return task_graph_status(
                task_graph, task_cache, kwargs.get("verbose"))

        raise ValueError(f"Unknown command {kwargs.get('command')}")


def task_graph_run(
    task_graph: TaskGraph,
    executor: TaskGraphExecutor | None = None,
    *,
    keep_going: bool = False,
) -> bool:
    """Execute (runs) the task_graph with the given executor."""
    no_errors = True
    for result_or_error in task_graph_run_with_results(
            task_graph, executor, keep_going=keep_going):
        if isinstance(result_or_error, Exception):
            no_errors = False
    return no_errors


def task_graph_run_with_results(
    task_graph: TaskGraph, executor: TaskGraphExecutor | None = None,
    *,
    keep_going: bool = False,
) -> Generator[Any, None, None]:
    """Run a task graph, yielding the results from each task."""
    if executor is None:
        executor = SequentialExecutor()
    tasks_iter = executor.execute(task_graph)
    for task, result_or_error in tasks_iter:
        if isinstance(result_or_error, Exception):
            if keep_going:
                print(f"Task {task.task_id} failed with:",
                      file=sys.stderr)
                traceback.print_exception(
                    None, value=result_or_error,
                    tb=result_or_error.__traceback__,
                    file=sys.stdout,
                )
            else:
                raise result_or_error
        yield result_or_error


def task_graph_all_done(task_graph: TaskGraph, task_cache: TaskCache) -> bool:
    """Check if the task graph is fully executed.

    When all tasks are already computed, the function returns True.
    If there are tasks, that need to run, the function returns False.
    """
    with task_graph as tasks:
        for task in tasks:
            record = task_cache.get_record(task_graph.get_task_desc(task))
            if record.type != CacheRecordType.COMPUTED:
                return False
    return True


def task_graph_status(
        task_graph: TaskGraph, task_cache: TaskCache,
        verbose: int | None) -> bool:
    """Show the status of each task from the task graph."""
    id_col_len = max(len(t.task_id) for t in task_graph.tasks)
    id_col_len = min(120, max(50, id_col_len))
    columns = ["TaskID", "Status"]
    print(f"{columns[0]:{id_col_len}s} {columns[1]}")
    for task in task_graph.tasks:
        record = task_cache.get_record(task_graph.get_task_desc(task))
        status = record.type.name
        msg = f"{task.task_id:{id_col_len}s} {status}"
        is_error = record.type == CacheRecordType.ERROR
        if is_error and not verbose:
            msg += " (-v to see exception)"
        print(msg)
        if is_error and verbose:
            traceback.print_exception(
                None, value=record.error,
                tb=record.error.__traceback__,
                file=sys.stdout,
            )
    return True
