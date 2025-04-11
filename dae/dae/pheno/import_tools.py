import argparse
import logging
import os
import pathlib
import sys

import yaml

from dae.pheno.common import PhenoImportConfig
from dae.pheno.pheno_import import get_gpf_instance, import_pheno_data
from dae.task_graph.cli_tools import TaskGraphCli

logger = logging.getLogger(__name__)


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype database import tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project",
        help="Configuration for the phenotype import",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        help="Set the verbosity level. [default: %(default)s]",
    )
    TaskGraphCli.add_arguments(parser, use_commands=False,
                               default_task_status_dir=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv
        if not argv[0].endswith("import_phenotypes"):
            logger.warning(
                "%s tool is deprecated! Use import_phenotypes.",
                argv[0],
            )
        argv = sys.argv[1:]
    parser = pheno_cli_parser()
    args = parser.parse_args(argv)

    project_path = pathlib.Path(args.project).absolute()
    raw_config = yaml.safe_load(project_path.read_text())

    input_dir = pathlib.Path(raw_config.get("input_dir", ""))
    if not input_dir.is_absolute():
        raw_config["input_dir"] = str(project_path.parent / input_dir)

    work_dir = pathlib.Path(raw_config["work_dir"])
    if not work_dir.is_absolute():
        raw_config["work_dir"] = str(project_path.parent / work_dir)

    import_config = PhenoImportConfig.model_validate(raw_config)
    gpf_instance = get_gpf_instance(import_config)
    delattr(args, "project")

    if args.task_status_dir is None:
        args.task_status_dir = os.path.join(
            raw_config["work_dir"], ".task-progress", import_config.id)
    if args.task_log_dir is None:
        args.task_log_dir = os.path.join(
            raw_config["work_dir"], ".task-log", import_config.id)

    import_pheno_data(import_config, gpf_instance, args)

    return 0
