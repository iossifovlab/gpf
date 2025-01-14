import argparse
import pathlib
import sys

import yaml

from dae.pheno.common import PhenoImportConfig
from dae.pheno.pheno_import import import_pheno_data
from dae.task_graph.cli_tools import TaskGraphCli


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
    TaskGraphCli.add_arguments(parser, use_commands=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]
    parser = pheno_cli_parser()
    args = parser.parse_args(argv)

    project_path = pathlib.Path(args.project).absolute()
    raw_config = yaml.safe_load(project_path.read_text())

    input_dir = pathlib.Path(raw_config.get("input_dir", ""))
    if not input_dir.is_absolute():
        raw_config["input_dir"] = str(project_path.parent / input_dir)

    output_dir = pathlib.Path(raw_config["output_dir"])
    if not output_dir.is_absolute():
        raw_config["output_dir"] = str(project_path.parent / output_dir)

    import_config = PhenoImportConfig.model_validate(raw_config)
    delattr(args, "project")
    import_pheno_data(import_config, args)

    return 0
