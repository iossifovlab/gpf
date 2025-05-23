import argparse
import logging
import sys

from dae.import_tools.import_tools import ImportProject
from dae.task_graph import TaskGraphCli
from dae.task_graph.executor import (
    AbstractTaskGraphExecutor,
    SequentialExecutor,
    task_graph_run,
)
from dae.utils import fs_utils
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Entry point for import tools when invoked as a cli tool."""
    if argv is None:
        argv = sys.argv
        if not argv[0].endswith("import_genotypes"):
            logger.warning(
                "%s tool is deprecated! Use import_genotypes.",
                argv[0],
            )
        argv = sys.argv[1:]
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
    if args.task_log_dir is None:
        args.task_log_dir = fs_utils.join(
            project.work_dir, ".task-log", project.study_id)

    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    if TaskGraphCli.process_graph(task_graph, **vars(args)):
        return 0
    return 1


def run_with_project(
    project: ImportProject,
    executor: AbstractTaskGraphExecutor | None = None,
) -> bool:
    """Run import with the given project."""
    if executor is None:
        executor = SequentialExecutor()
    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    return task_graph_run(task_graph, executor, keep_going=False)
