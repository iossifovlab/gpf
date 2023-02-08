import argparse
import textwrap

import yaml
from box import Box
from dae.task_graph.cache import TaskCache
from dae.task_graph.executor import DaskExecutor, TaskGraphExecutor, \
    SequentialExecutor, task_graph_run, task_graph_status

from dae.task_graph.graph import TaskGraph
from dae.dask.named_cluster import setup_client
from dae.dask.named_cluster import setup_client_from_config


class TaskGraphCli:
    """Takes care of creating a task graph executor and executing a graph."""

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser,
                      force_mode="optional",
                      default_task_status_dir=".",
                      use_commands=True):
        """Add arguments needed to execute a task graph."""
        executor_group = parser.add_argument_group(title="Task Graph Executor")
        # cluster_name
        # cluster_config_file
        executor_group.add_argument(
            "-j", "--jobs", type=int, default=None,
            help="Number of jobs to run in parallel. Defaults to the number "
            "of processors on the machine")

        executor_group.add_argument(
            "-N", "--dask-cluster-name", "--dcn",
            dest="dask_cluster_name",
            type=str, default=None,
            help="The named of the named dask cluster"
        )
        executor_group.add_argument(
            "-c", "--dccf", "--dask-cluster-config-file",
            dest="dask_cluster_config_file",
            type=str, default=None,
            help="dask cluster config file"
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
            help="Whether or not to keep executing in case of an error"
        )
        if force_mode == "optional":
            execution_mode_group.add_argument(
                "--force", "-f", default=False, action="store_true",
                help="Ignore precomputed state and always rerun all tasks."
            )
            execution_mode_group.add_argument(
                "-d", "--task-status-dir", "--tsd",
                default=default_task_status_dir,
                type=str, help="Directory to store the task progress."
            )
        else:
            assert force_mode == "always"

    @staticmethod
    def create_executor(**kwargs) -> TaskGraphExecutor:
        """Create a task graph executor according to the args specified."""
        args = Box(kwargs)
        task_cache = TaskCache.create(
            force=args.get("force"), cache_dir=args.get("task_status_dir"))

        if args.jobs == 1:
            assert args.dask_cluster_name is None
            assert args.dask_cluster_config_file is None
            return SequentialExecutor(task_cache=task_cache)

        assert args.dask_cluster_name is None or \
            args.dask_cluster_config_file is None
        if args.dask_cluster_config_file is not None:
            dask_cluster_config_file = args.dask_cluster_config_file
            assert dask_cluster_config_file is not None
            with open(dask_cluster_config_file) as conf_file:
                dask_cluster_config = yaml.safe_load(conf_file)
            print("THE CLUSTER CONFIG IS:", dask_cluster_config,
                  "loaded from", args.dask_cluster_config_file)
            client, _ = setup_client_from_config(
                dask_cluster_config,
                number_of_threads_param=args.jobs
            )
        else:
            client, _ = setup_client(args.dask_cluster_name,
                                     number_of_threads=args.jobs)
        print("Working with client:", client)
        return DaskExecutor(client, task_cache=task_cache)

    @staticmethod
    def process_graph(task_graph: TaskGraph, **kwargs) -> bool:
        """Process task_graph in according with the arguments in args."""
        args = Box(kwargs)

        if args.task_ids:
            task_graph = task_graph.prune(ids_to_keep=args.task_ids)

        with TaskGraphCli.create_executor(**kwargs) as executor:
            if args.command is None or args.command == "run":
                return task_graph_run(task_graph, executor, args.keep_going)

            if args.command in {"list", "status"}:
                res = task_graph_status(task_graph, executor, args.verbose)
                return res

            raise Exception("Unknown command")
