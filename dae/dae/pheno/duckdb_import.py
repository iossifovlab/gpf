import argparse
import os
import sys
import traceback
from copy import copy
from pathlib import Path
from typing import Any

import yaml

from dae.pheno.common import ImportConfig
from dae.pheno.prepare.pheno_prepare import PrepareVariables
from dae.task_graph.cli_tools import TaskGraphCli


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype database import tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        help="Set the verbosity level. [default: %(default)s]",
    )

    parser.add_argument(
        "-i",
        "--instruments",
        dest="instruments",
        help="The instruments dir",
        metavar="<instruments dir>",
    )

    parser.add_argument("--tab-separated",
        dest="tab_separated",
        action="store_true",
        help="Flag for whether the instrument files are tab separated.",
    )

    parser.add_argument("--inference-config",
        dest="inference_config",
        help="Measure classification type inference configuration",
    )

    parser.add_argument(
        "-p",
        "--pedigree",
        dest="pedigree",
        help="The pedigree file where families descriptions are located.",
        metavar="<pedigree file>",
    )

    parser.add_argument(
        "-o", "--output", dest="output",
        help="The output directory.", default="./output",
    )

    parser.add_argument(
        "--pheno-id", dest="pheno_name", help="output pheno database name.",
    )

    parser.add_argument(
        "--person-column",
        dest="person_column",
        default="person_id",
        help="The column in the instrument file containing the person ID.",
        metavar="<person column>",
    )

    TaskGraphCli.add_arguments(parser, use_commands=False)

    return parser


def verify_phenotype_data_name(input_name: str) -> str:
    phenotype_data_name = os.path.normpath(input_name)
    # check that the given pheno name is not a directory path
    split_path = os.path.split(phenotype_data_name)
    assert not split_path[0], f"'{phenotype_data_name}' is a directory path!"
    return phenotype_data_name


def generate_phenotype_data_config(
    args: argparse.Namespace, regressions: Any,
) -> dict[str, Any]:
    """Construct phenotype data configuration from command line arguments."""
    dbfile = os.path.join("%(wd)s", os.path.basename(args.pheno_db_filename))
    # pheno_db_path = os.path.dirname("%(wd)s")  # noqa
    config = {
        "vars": {"wd": "."},
        "phenotype_data": {
            "name": args.pheno_name,
            "dbfile": dbfile,
            "browser_images_url": "static/images/",
        },
    }
    if regressions:
        regressions_dict = regressions.to_dict()
        for reg in regressions_dict["regression"].values():
            if reg["measure_name"] is None:
                del reg["measure_name"]
            if reg["measure_names"] is None:
                del reg["measure_names"]
        config["regression"] = regressions_dict["regression"]
    return config


def parse_phenotype_data_config(args: argparse.Namespace) -> ImportConfig:
    """Construct phenotype data configuration from command line arguments."""
    config = ImportConfig()
    config.verbose = args.verbose
    config.instruments_dir = args.instruments
    config.instruments_tab_separated = args.tab_separated

    config.pedigree = args.pedigree
    config.output = args.output

    config.db_filename = args.pheno_db_filename
    config.person_column = args.person_column

    return config


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        # Setup argument parser

        parser = pheno_cli_parser()
        args = parser.parse_args(argv)
        if args.instruments is None:
            print("missing instruments directory parameter", sys.stderr)
            raise ValueError  # noqa: TRY301
        if args.pedigree is None:
            print("missing pedigree filename", sys.stderr)
            raise ValueError  # noqa: TRY301
        if args.pheno_name is None:
            print("missing pheno db name", sys.stderr)
            raise ValueError  # noqa: TRY301

        output_dir = args.output

        os.makedirs(output_dir, exist_ok=True)

        args.pheno_db_filename = os.path.join(
            output_dir, f"{args.pheno_name}.db",
        )
        if os.path.exists(args.pheno_db_filename):
            os.remove(args.pheno_db_filename)

        config = parse_phenotype_data_config(args)
        os.makedirs(os.path.join(config.output, "parquet"), exist_ok=True)

        inference_configs: dict[str, Any] = {}
        if args.inference_config:
            inference_configs = yaml.safe_load(
                Path(args.inference_config).read_text(),
            )

        prep = PrepareVariables(config, inference_configs)
        prep.build_tables()
        print(" PEDIGREE START")
        import time
        start = time.time()
        prep.build_pedigree(args.pedigree)
        print(f"LOADED PEDIGREE {time.time() - start}")
        kwargs = copy(vars(args))
        kwargs["skip_pheno_common"] = True
        prep.build_variables(
            args.instruments, None, **kwargs,
        )

    except KeyboardInterrupt:
        return 0
    except ValueError as e:
        traceback.print_exc()

        program_name = "pheno_import.py"
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
