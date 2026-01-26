import argparse
import logging
import sys

from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
)
from dae.import_tools.import_tools import ImportProject
from dae.task_graph.cli_tools import TaskGraphCli, task_graph_run
from dae.task_graph.executor import TaskGraphExecutor
from dae.task_graph.sequential_executor import SequentialExecutor
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
    context_providers_add_argparser_arguments(
        parser, skip_cli_annotation_context=True)
    VerbosityConfiguration.set_arguments(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)
    context_providers_init(
        **vars(args), skip_cli_annotation_context=True)

    genomic_context = get_genomic_context()

    project = ImportProject.build_from_file(
        args.config,
        genomic_context=genomic_context)

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
    executor: TaskGraphExecutor | None = None,
) -> bool:
    """Run import with the given project."""
    if executor is None:
        executor = SequentialExecutor()
    storage = project.get_import_storage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph.input_files.extend(project.config_filenames)

    return task_graph_run(task_graph, executor, keep_going=False)
