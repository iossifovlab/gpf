#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import traceback
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from pheno.common import default_config, dump_config, check_config_pheno_db
from pheno.prepare.ped_prepare import PrepareVariables
from tools.pheno2browser import build_pheno_browser


def pheno_cli_parser():
    parser = ArgumentParser(
        description="simple phenotype database import tool",
        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        "-v", "--verbose", dest="verbose",
        action="count", help="set verbosity level [default: %(default)s]")
    parser.add_argument(
        "-i", "--instruments",
        dest="instruments",
        help="directory where all instruments are located",
        metavar="<instruments dir>")
    parser.add_argument(
        "-p", "--pedigree",
        dest="pedigree",
        help="pedigree file where families descriptions are located",
        metavar="<pedigree file>")

    parser.add_argument(
        '-d', '--pheno-db-filename',
        dest='pheno_db_filename',
        help='pheno DB ouput file',
        metavar='<pheno db filename>')

    parser.add_argument(
        "-P", "--pheno",
        dest="pheno_name",
        help="pheno database name"
    )
    parser.add_argument(
        '-b', '--browser-dir',
        dest='browser_dir',
        help='output browser dir',
        metavar='<browser dir>')

    parser.add_argument(
        '--age',
        dest="age",
        help="pheno measure ID represenging age at assesment",
        type=str
    )

    parser.add_argument(
        '--nonverbal_iq',
        dest="nonverbal_iq",
        help="pheno measure ID representing non-verbal IQ measure",
        type=str,
    )

    parser.add_argument(
        "--force",
        dest="force",
        help="overwrites already existing pheno db file",
        action="store_true"
    )

    return parser


def parse_pheno_db_config(args):
    config = default_config()
    config.verbose = args.verbose
    config.instruments.dir = args.instruments

    config.pedigree = args.pedigree

    config.db.filename = args.pheno_db_filename

    dump_config(config)
    check_config_pheno_db(config)

    return config


def main(argv):

    try:
        # Setup argument parser

        parser = pheno_cli_parser()
        args = parser.parse_args(argv)
        if args.instruments is None:
            print("missing instruments directory parameter", sys.stderr)
            raise ValueError()
        if args.pedigree is None:
            print("missing pedigree filename", sys.stderr)
            raise ValueError()
        if args.pheno_name is None:
            print("missing pheno db name", sys.stderr)
            raise ValueError()

        if args.pheno_db_filename is None:
            args.pheno_db_filename = os.path.join(
                os.path.curdir,
                "{}.db".format(args.pheno_name)
            )
        if os.path.exists(args.pheno_db_filename):
            if not args.force:
                print(
                    "pheno db filename already exists:",
                    args.pheno_db_filename)
                raise ValueError()
            else:
                os.remove(args.pheno_db_filename)

        if args.browser_dir is None:
            args.browser_dir = os.path.join(
                os.path.dirname(args.pheno_db_filename),
                "browser",
                args.pheno_name
            )
        if not os.path.exists(args.browser_dir):
            os.makedirs(args.browser_dir)

        config = parse_pheno_db_config(args)
        prep = PrepareVariables(config)
        prep.build_pedigree(args.pedigree)
        prep.build_variables(args.instruments)

        build_pheno_browser(
            args.pheno_db_filename, args.pheno_name,
            args.browser_dir,
            args.age, args.nonverbal_iq
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
