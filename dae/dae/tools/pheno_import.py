#!/usr/bin/env python

import argparse
import os
import sys
import traceback
from copy import copy
from pathlib import Path
from typing import Any

import yaml
from box import Box
from pydantic import BaseModel

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.pheno.prepare.measure_classifier import InferenceConfig
from dae.pheno.prepare.pheno_prepare import PrepareVariables
from dae.task_graph.cli_tools import TaskGraphCli
from dae.tools.pheno2browser import build_pheno_browser


class ImportConfig(BaseModel):
    report_only: bool = False
    instruments_tab_separated: bool = False
    person_column: str = "personId"
    db_filename: str = "pheno.db"
    default_inference: InferenceConfig = InferenceConfig()
    output: str = "output"
    verbose: int = 0
    instruments_dir: str = ""
    pedigree: str = ""



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
        help="The directory where all instruments are located.",
        metavar="<instruments dir>",
    )

    parser.add_argument("--tab-separated",
        dest="tab_separated",
        action="store_true",
        help="Flag for whether the instrument files are tab separated.",
    )

    parser.add_argument("--skip-pheno-common",
        dest="skip_pheno_common",
        action="store_true",
        help="Flag for skipping the building of the pheno common instrument.",
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
        "--data-dictionary",
        dest="data_dictionary",
        help="The tab separated file that contains descriptions of measures.",
        metavar="<data dictionary file>",
    )

    parser.add_argument(
        "-o", "--output", dest="output",
        help="The output directory.", default="./output",
    )

    parser.add_argument(
        "--pheno-id", dest="pheno_name", help="output pheno database name.",
    )

    parser.add_argument(
        "--regression",
        help="absolute path to a regression configuration file",
    )
    parser.add_argument(
        "--person-column",
        dest="person_column",
        default="person_id",
        help="The column in instruments files containing the person ID.",
        metavar="<person column>",
    )

    parser.add_argument(
        "--continue",
        dest="browser_only",
        help="Perform the second browser generation step on an existing DB.",
        action="store_true",
    )

    parser.add_argument(
        "--import-only",
        dest="import_only",
        help="Perform the data import step only.",
        action="store_true",
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


def parse_phenotype_data_config(args: argparse.Namespace) -> Box:
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


def build_browser(
    args: argparse.Namespace, regressions: Box | None,
) -> None:
    """Perform browser data build step."""
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    kwargs = copy(vars(args))
    pheno_db_filename = args.pheno_db_filename
    del kwargs["pheno_db_filename"]
    pheno_name = args.pheno_name
    del kwargs["pheno_name"]

    build_pheno_browser(
        pheno_db_filename,
        pheno_name,
        output_dir,
        regressions,
        **kwargs,
    )

    pheno_conf_path = os.path.join(
        output_dir, f"{pheno_name}.yaml",
    )

    config = yaml.dump(generate_phenotype_data_config(args, regressions))
    Path(pheno_conf_path).write_text(config)


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
        if args.import_only and args.browser_only:
            raise ValueError(  # noqa: TRY301
                "Both import only and continue used!")

        output_dir = args.output

        os.makedirs(output_dir, exist_ok=True)

        args.pheno_db_filename = os.path.join(
            output_dir, f"{args.pheno_name}.db",
        )
        if args.regression:
            regressions = GPFConfigParser.load_config(
                args.regression, regression_conf_schema,
            )
        else:
            regressions = None

        if args.browser_only:
            assert os.path.exists(args.pheno_db_filename), \
                f"{args.pheno_db_filename} does not exist!"
            build_browser(args, regressions)
            return 0

        if os.path.exists(args.pheno_db_filename):
            if not args.force:
                print(
                    "pheno db filename already exists:", args.pheno_db_filename,
                )
                raise ValueError  # noqa: TRY301
            os.remove(args.pheno_db_filename)

        config = parse_phenotype_data_config(args)
        os.makedirs(os.path.join(config.output, "parquet"), exist_ok=True)

        inference_configs: dict[str, InferenceConfig] = {}
        if args.inference_config:
            inference_configs: dict[str, InferenceConfig] = yaml.safe_load(
                Path(args.inference_config).read_text()
            )

        prep = PrepareVariables(config, inference_configs)
        prep.build_pedigree(args.pedigree)
        kwargs = copy(vars(args))
        prep.build_variables(
            args.instruments, args.data_dictionary, **kwargs
        )

        if not args.import_only:
            build_browser(args, regressions)
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
