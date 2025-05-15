import argparse
import logging
import subprocess
import sys
from pathlib import Path

import yaml

from dae.task_graph.cli_tools import TaskGraphCli
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger(__name__)


def cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="Import study, build browser and package it in one.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    VerbosityConfiguration.set_arguments(parser)
    parser.add_argument(
        "pheno_import_project",
        nargs="?",
        type=str,
        default=None,
        help="Path to pheno_import_project file.",
    )
    parser.add_argument(
        "package_destination",
        type=str,
        default=None,
        help="Path to dir where to save the packaged pheno data.",
    )

    TaskGraphCli.add_arguments(parser, use_commands=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    parser = cli_parser()
    args = parser.parse_args(argv)

    assert args.pheno_import_project is not None
    assert args.package_destination is not None

    project_file_path = Path(args.pheno_import_project).absolute()
    project_path = Path(args.pheno_import_project).absolute().cwd()
    destination = Path(args.package_destination).absolute()
    pheno_id = yaml.safe_load(
        Path(args.pheno_import_project).absolute().read_text(),
    )["id"]
    output = "pheno_output"

    preprocess_cmd = f"{project_path}/preprocess.sh -i data_full"
    import_cmd = f"import_phenotypes {project_file_path!s} --no-cache --force"
    build_cmd = f"build_pheno_browser {pheno_id} --pheno-db-dir {output}"
    package_cmd = f"tar -cvf {pheno_id}.tar -C {output} ."
    clean_cmd = f"rm -rf {output}"
    move_cmd = f"mv {pheno_id}.tar {destination}/{pheno_id}.tar"

    color = "\033[1m" + "\033[95m"
    end_color = "".join(["\033[0m"] * 2)

    print(f"{color}Preprocessing data...{end_color}")
    subprocess.run(preprocess_cmd.split(" "), check=True)

    print(f"{color}Importing phenotype data...{end_color}")
    subprocess.run(import_cmd.split(" "), check=True)

    print(f"{color}Building phenotype browser...{end_color}")
    subprocess.run(build_cmd.split(" "), check=True)

    print(f"{color}Packaging data...{end_color}")
    subprocess.run(package_cmd.split(" "), check=True)

    print(f"{color}Cleaning leftover files...{end_color}")
    subprocess.run(clean_cmd.split(" "), check=True)

    print(f"{color}Moving package to destination...{end_color}")
    subprocess.run(move_cmd.split(" "), check=True)
    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
