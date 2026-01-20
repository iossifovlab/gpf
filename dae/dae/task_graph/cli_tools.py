import argparse
import logging
import textwrap
from typing import Any

import yaml
from box import Box

from dae.dask.named_cluster import setup_client, setup_client_from_config
from dae.task_graph.cache import NoTaskCache, TaskCache
from dae.task_graph.executor import (
    DaskExecutor,
    SequentialExecutor,
    TaskGraphExecutor,
    ThreadedTaskExecutor,
    task_graph_all_done,
    task_graph_run,
    task_graph_status,
)
from dae.task_graph.graph import TaskGraph

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
            "--thread-pool", "--tp",
            dest="use_thread_pool", action="store_true",
            help="Use a thread pool executor with the specified number of "
            "threads instead of a dask distributed executor.",
        )
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
            execution_mode_group.add_argument(
                "--fork-tasks", "--fork-task", "--fork",
                dest="fork_tasks", action="store_true",
                help="Whether to fork a new worker process for each task",
            )

        else:
            assert not task_progress_mode, \
                "task_progress_mode must be False if no cache is used"

    @staticmethod
    def create_executor(
            task_cache: TaskCache | None = None,
            **kwargs: Any) -> TaskGraphExecutor:
        """Create a task graph executor according to the args specified."""
        args = Box(kwargs)

        if task_cache is None:
            task_cache = NoTaskCache()

        if args.jobs == 1:
            assert args.dask_cluster_name is None
            assert args.dask_cluster_config_file is None
            return SequentialExecutor(task_cache=task_cache, **kwargs)

        if args.use_thread_pool or args.use_process_pool:
            assert args.dask_cluster_name is None
            assert args.dask_cluster_config_file is None
            pool_type = "process_pool"
            if args.use_thread_pool:
                pool_type = "thread_pool"
            return ThreadedTaskExecutor(
                n_threads=args.jobs,
                task_cache=task_cache,
                pool_type=pool_type,
                **kwargs)

        assert args.dask_cluster_name is None or \
            args.dask_cluster_config_file is None
        if args.dask_cluster_config_file is not None:
            dask_cluster_config_file = args.dask_cluster_config_file
            assert dask_cluster_config_file is not None
            with open(dask_cluster_config_file) as conf_file:
                dask_cluster_config = yaml.safe_load(conf_file)
            logger.info(
                "THE CLUSTER CONFIG IS: %s; loaded from: %s",
                dask_cluster_config,
                args.dask_cluster_config_file)
            client, _ = setup_client_from_config(
                dask_cluster_config,
                number_of_workers=args.jobs,
            )
        else:
            client, _ = setup_client(
                args.dask_cluster_name,
                number_of_workers=args.jobs)

        logger.info("Working with client: %s", client)
        return DaskExecutor(client, task_cache=task_cache, **kwargs)

    @staticmethod
    def process_graph(
        task_graph: TaskGraph, *,
        task_progress_mode: bool = True,
        **kwargs: Any,
    ) -> bool:
        """Process task_graph in according with the arguments in args.

        Return true if the graph get's successfully processed.
        """
        args = Box(kwargs)

        if args.task_ids:
            task_graph = task_graph.prune(ids_to_keep=args.task_ids)

        force = args.get("force", False)
        task_cache = TaskCache.create(
            task_progress_mode=task_progress_mode,
            force=force,
            cache_dir=args.get("task_status_dir"),
        )

        if args.command is None or args.command == "run":
            if task_graph_all_done(task_graph, task_cache):
                logger.warning(
                    "All tasks are already COMPUTED; nothing to compute")
                return True
            with TaskGraphCli.create_executor(task_cache, **kwargs) as xtor:
                return task_graph_run(
                    task_graph, xtor, keep_going=args.keep_going)

        if args.command in {"list", "status"}:
            return task_graph_status(task_graph, task_cache, args.verbose)

        raise ValueError(f"Unknown command {args.command}")
