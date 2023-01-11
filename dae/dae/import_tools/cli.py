import argparse
import sys
import textwrap
import traceback
from dae.import_tools.import_tools import ImportProject
from dae.task_graph.cache import CacheRecordType, FileTaskCache

from dae.task_graph.executor import \
    DaskExecutor, SequentialExecutor
from dae.dask.client_factory import DaskClient
from dae.utils import fs_utils


def main(argv=None):
    """Entry point for import tools when invoked as a cli tool."""
    parser = argparse.ArgumentParser(
        description="Import datasets into GPF",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("config", type=str,
                        help="Path to the import configuration")
    parser.add_argument(
        "command", choices=["run", "list", "status"], default="run", nargs="?",
        help=textwrap.dedent("""\
            Command to execute on the import configuration.
            run - runs the import process
            list - lists the tasks to be executed but doesn't run them
            status - synonym for list
        """),
    )
    parser.add_argument("--task-id", dest="task_ids", type=str, nargs="+")
    parser.add_argument(
        "--force", "-f", default=False, action="store_true",
        help="Ignore precomputed state and always rerun the entire import"
    )
    parser.add_argument(
        "--keep-going", default=False, action="store_true",
        help="Whether or not to keep executing in case of an error"
    )
    parser.add_argument(
        "--verbose", "-v", default=False, action="store_true",
        help="Enable verbose output"
    )
    DaskClient.add_arguments(parser)
    args = parser.parse_args(argv or sys.argv[1:])

    project = ImportProject.build_from_file(args.config)
    task_cache = _create_task_cache(args, project)

    if args.command is None or args.command == "run":
        return _cmd_run(args, project, task_cache)
    if args.command in {"list", "status"}:
        return _cmd_list(args, project, task_cache)
    parser.exit(message=f"Unknown command {args.command}\n")
    return 0


def _cmd_run(args, project, task_cache):
    ids_to_run = args.task_ids or []
    if args.jobs == 1:
        executor = SequentialExecutor(task_cache=task_cache)
        return run_with_project(
            project, executor, ids_to_run=ids_to_run,
            keep_going=args.keep_going
        )

    dask_client = DaskClient.from_arguments(args)
    if dask_client is None:
        sys.exit(1)
    with dask_client as client:
        executor = DaskExecutor(client, task_cache=task_cache)
        return run_with_project(
            project, executor, ids_to_run=ids_to_run,
            keep_going=args.keep_going
        )


def _cmd_list(args, project, task_cache):
    storage = project.get_import_storage()
    print("Generating Task Graph ...", end="")
    task_graph = storage.generate_import_task_graph(project)
    print("Done")
    task_graph.input_files.extend(project.config_filenames)
    task_graph = _prune_tasks(task_graph, args.task_ids or [])

    task_cache.set_task_graph(task_graph)
    id_col_len = max(len(t.task_id) for t in task_graph.tasks)
    id_col_len = min(120, max(50, id_col_len))
    if not args.verbose:
        columns = ["TaskID", "Status"]
        print(f"{columns[0]:{id_col_len}s} {columns[1]}")
    for task in task_graph.tasks:
        record = task_cache.get_record(task)
        status = record.type.name
        is_error = record.type == CacheRecordType.ERROR

        if args.verbose:
            print(f"Task-Id={task.task_id}")
            print(f"Status={status}")
        else:
            id_and_status = f"{task.task_id:{id_col_len}s} {status}"
            if is_error:
                id_and_status += " (-v to see exception)"
            print(id_and_status)

        if args.verbose:
            task_dep_ids_str = ",".join(dep.task_id for dep in task.deps)
            print(f"Deps=[{task_dep_ids_str}]")
            inputs = task.input_files if task.deps else task_graph.input_files
            inputs_str = ",".join(inputs)
            print(f"Input-files=[{inputs_str}]")
        if is_error and args.verbose:
            print("Error=", end="")
            traceback.print_exception(
                etype=None, value=record.error,
                tb=record.error.__traceback__,
                file=sys.stdout
            )
        if args.verbose:
            print()


def _prune_tasks(graph, ids_to_run):
    if not ids_to_run:
        return graph

    try:
        return graph.prune(ids_to_keep=ids_to_run)
    except KeyError as exp:
        print(f"Task IDs {exp.args[0]} not found", file=sys.stderr)
        sys.exit(1)


def _add_task_deps(task, task_set):
    for dep in task.deps:
        if dep not in task_set:
            task_set.add(dep)
            _add_task_deps(dep, task_set)


def run_with_project(project, executor=SequentialExecutor(), ids_to_run=None,
                     keep_going=False):
    """Import the project using the provided executor."""
    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)
    task_graph = _prune_tasks(task_graph, ids_to_run)

    any_errors = False

    tasks_iter = executor.execute(task_graph)
    last_stagenames = _get_current_stagenames(executor)
    _print_stagenames(last_stagenames)
    for task, result_or_error in tasks_iter:
        if isinstance(result_or_error, Exception):
            if keep_going:
                print(f"Task {task.task_id} failed with:", file=sys.stderr)
                traceback.print_exception(
                    etype=None, value=result_or_error,
                    tb=result_or_error.__traceback__
                )
                any_errors = True
            else:
                raise result_or_error
        current_stagenames = _get_current_stagenames(executor)
        if current_stagenames != last_stagenames:
            last_stagenames = current_stagenames
            _print_stagenames(last_stagenames)

    return 1 if any_errors else 0


def _get_current_stagenames(executor):
    # we use the task name is also the stagename
    return {
        t.task_id
        for t in executor.get_active_tasks()
        if t.task_id is not None
    }


def _print_stagenames(stagenames):
    if stagenames:
        stagenames_str = ", ".join(stagenames)
        print(f"Executing stage: {stagenames_str}")


def _create_task_cache(args, project):
    cache_dir = fs_utils.join(
        project.work_dir, ".task-progress", project.study_id
    )
    return FileTaskCache(force=args.force, cache_dir=cache_dir)
