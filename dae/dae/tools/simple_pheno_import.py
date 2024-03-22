#!/usr/bin/env python

import argparse
import os
import sys
import traceback
from typing import Any, Optional

import toml
from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pheno.common import (
    check_phenotype_data_config,
    default_config,
    dump_config,
)
from dae.pheno.prepare.pheno_prepare import PrepareVariables
from dae.tools.pheno2browser import build_pheno_browser


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for simple phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="simple phenotype database import tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        help="set verbosity level [default: %(default)s]",
    )

    parser.add_argument(
        "-i",
        "--instruments",
        dest="instruments",
        help="directory where all instruments are located",
        metavar="<instruments dir>",
    )

    parser.add_argument(
        "-p",
        "--pedigree",
        dest="pedigree",
        help="pedigree file where families descriptions are located",
        metavar="<pedigree file>",
    )

    parser.add_argument(
        "-d",
        "--data-dictionary",
        dest="data_dictionary",
        help="tab separated file that contains descriptions of measures",
        metavar="<data dictionary file>",
    )

    parser.add_argument(
        "-o", "--pheno", dest="pheno_name", help="output pheno database name",
    )

    parser.add_argument(
        "--regression", help="absolute path to a regression configuration file",
    )
    parser.add_argument(
        "--person-column",
        dest="person_column",
        default="person_id",
        help="The column in instruments files containing the person ID",
        metavar="<person column>"
    )

    parser.add_argument(
        "--force",
        dest="force",
        help="overwrites already existing pheno db file",
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
    browser_dbfile = os.path.join(
        "%(wd)s", "browser", f"{args.pheno_name}_browser.db",
    )
    config = {
        "vars": {"wd": "."},
        "phenotype_data": {
            "name": args.pheno_name,
            "dbfile": dbfile,
            "browser_images_url": f"/static/images/{args.pheno_name}/",
        },
    }
    if regressions:
        regressions_dict = regressions.to_dict()
        config["regression"] = regressions_dict["regression"]
    return config


def parse_phenotype_data_config(args: argparse.Namespace) -> Box:
    """Construct phenotype data configuration from command line arguments."""
    config = default_config()
    config.verbose = args.verbose
    config.instruments.dir = args.instruments

    config.pedigree = args.pedigree

    config.db.filename = args.pheno_db_filename
    config.person.column = args.person_column

    dump_config(config)
    check_phenotype_data_config(config)

    return config


def main(argv: Optional[list[str]] = None) -> int:
    """Run simple phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        # Setup argument parser

        gpf_instance = GPFInstance.build()
        dae_conf = gpf_instance.dae_config

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

        args.pheno_name = verify_phenotype_data_name(args.pheno_name)

        pheno_db_dir = os.path.join(
            dae_conf.phenotype_data.dir, args.pheno_name,
        )
        if not os.path.exists(pheno_db_dir):
            os.makedirs(pheno_db_dir)

        args.pheno_db_filename = os.path.join(
            pheno_db_dir, f"{args.pheno_name}.db",
        )
        if os.path.exists(args.pheno_db_filename):
            if not args.force:
                print(
                    "pheno db filename already exists:", args.pheno_db_filename,
                )
                raise ValueError
            os.remove(args.pheno_db_filename)

        args.browser_dir = os.path.join(pheno_db_dir, "browser")
        if not os.path.exists(args.browser_dir):
            os.makedirs(args.browser_dir)

        config = parse_phenotype_data_config(args)
        os.makedirs(config.output, exist_ok=True)
        if args.regression:
            regressions = GPFConfigParser.load_config(
                args.regression, regression_conf_schema,
            )
        else:
            regressions = None

        prep = PrepareVariables(config)
        prep.build_pedigree(args.pedigree)
        prep.build_variables(args.instruments, args.data_dictionary)

        # prep.db.clear_instrument_values_tables(drop=True)
        # prep.db.build_instrument_values_tables()
        # prep.db.populate_instrument_values_tables()


        build_pheno_browser(
            args.pheno_db_filename,
            args.pheno_name,
            args.browser_dir,
            regressions,
        )

        pheno_conf_path = os.path.join(
            pheno_db_dir, f"{args.pheno_name}.conf",
        )

        with open(pheno_conf_path, "w") as pheno_conf_file:
            pheno_conf_file.write(
                toml.dumps(generate_phenotype_data_config(args, regressions)),
            )

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        traceback.print_exc()

        program_name = "simple_pheno_import.py"
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    main(sys.argv[1:])
