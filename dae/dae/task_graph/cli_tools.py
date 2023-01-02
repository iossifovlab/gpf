import sys
import argparse
import textwrap
import traceback
from dae.task_graph.cache import CacheRecordType, FileTaskCache
from dae.task_graph.executor import DaskExecutor
from dae.task_graph.executor import SequentialExecutor

from dae.task_graph.graph import TaskGraph
from dae.dask.named_cluster import setup_client


def add_arguments(parser: argparse.ArgumentParser):
    executor_group = parser.add_argument_group(title="Task Graph Executor")
    executor_group.add_argument(
            "-j", "--jobs", type=int, default=None,
            help="Number of jobs to run in parallel. Defaults to the number "
            "of processors on the machine")
    
    execution_mode_group = parser.add_argument_group(title="Execution Mode")
    execution_mode_group.add_argument("command",
                        choices=["run", "list", "status"],
                        default="run", nargs="?",
                        help=textwrap.dedent("""\
                Command to execute on the import configuration.
                run - runs the import process
                list - lists the tasks to be executed but doesn't run them
                status - synonym for list
            """),
                        )
    execution_mode_group.add_argument("--task-id", dest="task_ids", type=str, nargs="+")
    execution_mode_group.add_argument(
        "--force", "-f", default=False, action="store_true",
        help="Ignore precomputed state and always rerun the entire import"
    )
    execution_mode_group.add_argument(
        "--keep-going", default=False, action="store_true",
        help="Whether or not to keep executing in case of an error"
    )


def process_graph(args: argparse.Namespace, task_graph: TaskGraph) -> bool:
    task_cache = FileTaskCache(force=args.force, cache_dir=".")

    if args.task_ids:
        task_graph = task_graph.prune(ids_to_keep=args.task_ids)

    if args.command is None or args.command == "run":
        if args.jobs == 1:
            executor = SequentialExecutor(task_cache=task_cache)
        else:
            client, _, _ = setup_client(number_of_threads=args.jobs)
            executor = DaskExecutor(client, task_cache=task_cache)

        no_errors = True
        tasks_iter = executor.execute(task_graph)
        for task, result_or_error in tasks_iter:
            if isinstance(result_or_error, Exception):
                if args.keep_going:
                    print(f"Task {task.task_id} failed with:", file=sys.stderr)
                    no_errors = False
                else:
                    raise result_or_error
        return no_errors
    elif args.command == "list":
        task_cache.set_task_graph(task_graph)
        id_col_len = max(len(t.task_id) for t in task_graph.tasks)
        id_col_len = min(120, max(50, id_col_len))
        columns = ["TaskID", "Status"]
        print(f"{columns[0]:{id_col_len}s} {columns[1]}")
        for task in task_graph.tasks:
            record = task_cache.get_record(task)
            status = record.type.name
            msg = f"{task.task_id:{id_col_len}s} {status}"
            is_error = record.type == CacheRecordType.ERROR
            if is_error and not args.verbose:
                msg += " (-v to see exception)"
            print(msg)
            if is_error and args.verbose:
                traceback.print_exception(
                    etype=None, value=record.error,
                    tb=record.error.__traceback__,
                    file=sys.stdout
                )
    else:
        raise Exception("Unknown command")

    # if args.command in {"list", "status"}:
    #     return _cmd_list(args, project, task_cache)
    # return 0
