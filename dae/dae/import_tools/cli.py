import argparse
import sys

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.import_tools.import_tools import ImportProject

from dae.task_graph.executor import SequentialExecutor
from dae.utils import fs_utils

from dae.task_graph import TaskGraphCli


def main(argv=None):
    """Entry point for import tools when invoked as a cli tool."""
    parser = argparse.ArgumentParser(
        description="Import datasets into GPF",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("config", type=str,
                        help="Path to the import configuration")
    TaskGraphCli.add_arguments(parser, default_task_status_dir=None)
    VerbosityConfiguration.set_argumnets(parser)
    args = parser.parse_args(argv or sys.argv[1:])
    VerbosityConfiguration.set(args)

    project = ImportProject.build_from_file(args.config)

    if args.task_status_dir is None:
        args.task_status_dir = fs_utils.join(
            project.work_dir, ".task-progress", project.study_id)

    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    return TaskGraphCli.process_graph(args, task_graph)


def run_with_project(project, executor=SequentialExecutor()):
    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    return TaskGraphCli.run(task_graph, executor, keep_going=False)
