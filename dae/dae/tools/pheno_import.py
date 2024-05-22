#!/usr/bin/env python

import argparse
import os
import sys
import traceback
from typing import Any, Optional

import yaml
from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.pheno.common import (
    check_phenotype_data_config,
    default_config,
    dump_config,
)
from dae.pheno.prepare.pheno_prepare import PrepareVariables
from dae.tools.pheno2browser import build_pheno_browser


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

    parser.add_argument(
        "--tab-separated",
        dest="tab_separated",
        action="store_true",
        help="Flag for whether the instrument files are tab separated.",
    )

    parser.add_argument(
        "-p",
        "--pedigree",
        dest="pedigree",
        help="The pedigree file where families descriptions are located.",
        metavar="<pedigree file>",
    )

    parser.add_argument(
        "-d",
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
        "--force",
        dest="force",
        help="overwrites already existing pheno db file.",
        action="store_true",
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
    config = default_config()
    config.verbose = args.verbose
    config.instruments.dir = args.instruments
    config.instruments.tab_separated = args.tab_separated

    config.pedigree = args.pedigree
    config.output = args.output

    config.db.filename = args.pheno_db_filename
    config.person.column = args.person_column

    dump_config(config)
    check_phenotype_data_config(config)

    return config


def build_browser(
    args: argparse.Namespace, regressions: Optional[Box],
) -> None:
    """Perform browser data build step."""
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    build_pheno_browser(
        args.pheno_db_filename,
        args.pheno_name,
        output_dir,
        regressions,
    )

    pheno_conf_path = os.path.join(
        output_dir, f"{args.pheno_name}.yaml",
    )

    with open(pheno_conf_path, "w") as pheno_conf_file:
        pheno_conf_file.write(yaml.dump(
            generate_phenotype_data_config(args, regressions),
        ))


def main(argv: Optional[list[str]] = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        # Setup argument parser

        parser = pheno_cli_parser()
        args = parser.parse_args(argv)
        if args.instruments is None:
            print("missing instruments directory parameter", sys.stderr)
            raise ValueError
        if args.pedigree is None:
            print("missing pedigree filename", sys.stderr)
            raise ValueError
        if args.pheno_name is None:
            print("missing pheno db name", sys.stderr)
            raise ValueError
        if args.import_only and args.browser_only:
            raise ValueError("Both import only and continue used!")

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
                raise ValueError
            os.remove(args.pheno_db_filename)

        config = parse_phenotype_data_config(args)
        os.makedirs(os.path.join(config.output, "parquet"), exist_ok=True)

        prep = PrepareVariables(config)
        prep.build_pedigree(args.pedigree)
        prep.build_variables(args.instruments, args.data_dictionary)

        if not args.import_only:
            build_browser(args, regressions)

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        traceback.print_exc()

        program_name = "pheno_import.py"
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    main(sys.argv[1:])
