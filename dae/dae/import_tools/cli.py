import argparse
import sys
from typing import List, Optional

from dae.import_tools.import_tools import ImportProject
from dae.task_graph import TaskGraphCli
from dae.task_graph.executor import (
    AbstractTaskGraphExecutor,
    SequentialExecutor,
    task_graph_run,
)
from dae.utils import fs_utils
from dae.utils.verbosity_configuration import VerbosityConfiguration


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for import tools when invoked as a cli tool."""
    parser = argparse.ArgumentParser(
        description="Import datasets into GPF",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("config", type=str,
                        help="Path to the import configuration")
    TaskGraphCli.add_arguments(parser, default_task_status_dir=None)
    VerbosityConfiguration.set_arguments(parser)
    args = parser.parse_args(argv or sys.argv[1:])
    VerbosityConfiguration.set(args)

    project = ImportProject.build_from_file(args.config)

    if args.task_status_dir is None:
        args.task_status_dir = fs_utils.join(
            project.work_dir, ".task-progress", project.study_id)

    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    if TaskGraphCli.process_graph(task_graph, **vars(args)):
        return 0
    return 1


def run_with_project(
    project: ImportProject,
    executor: Optional[AbstractTaskGraphExecutor] = None,
) -> bool:
    """Run import with the given project."""
    if executor is None:
        executor = SequentialExecutor()
    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    return task_graph_run(task_graph, executor, keep_going=False)
