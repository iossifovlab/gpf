#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import traceback
import configparser
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from dae.pheno.common import default_config, dump_config, check_config_pheno_db
from dae.pheno.prepare.ped_prepare import PrepareVariables
from dae.tools.pheno2browser import build_pheno_browser

from dae.configurable_entities.configuration import DAEConfig


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
        "-d", "--data-dictionary",
        dest="data_dictionary",
        help="tab separated file that contains descriptions of measures",
        metavar="<data dictionary file>")

    parser.add_argument(
        "-o", "--pheno",
        dest="pheno_name",
        help="output pheno database name"
    )

    parser.add_argument(
        '--regression',
        help="absolute path to a regression configuration file"
    )

    parser.add_argument(
        "--force",
        dest="force",
        help="overwrites already existing pheno db file",
        action="store_true"
    )

    return parser


def generate_pheno_db_config(args):
    config = configparser.ConfigParser()
    config['phenoDB'] = {}
    section = config['phenoDB']
    section['name'] = args.pheno_name
    section['dbfile'] = os.path.basename(args.pheno_db_filename)
    # TODO
    # Should the regression config be written to the pheno db config?
    section['browser_dbfile'] = \
        'browser/{}_browser.db'.format(args.pheno_name)
    section['browser_images_dir'] = 'browser/images'
    section['browser_images_url'] = \
        '/static/{}/browser/images/'.format(args.pheno_name)
    return config


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

        dae_conf = DAEConfig.make_config()

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

        pheno_db_dir = os.path.join(
            dae_conf.pheno_dir,
            args.pheno_name
        )

        if not os.path.exists(pheno_db_dir):
            os.makedirs(pheno_db_dir)

        args.pheno_db_filename = os.path.join(
            pheno_db_dir,
            "{}.db".format(args.pheno_name)
        )
        if os.path.exists(args.pheno_db_filename):
            if not args.force:
                print("pheno db filename already exists:",
                      args.pheno_db_filename)
                raise ValueError()
            else:
                os.remove(args.pheno_db_filename)

        args.browser_dir = os.path.join(
            pheno_db_dir,
            "browser"
        )
        if not os.path.exists(args.browser_dir):
            os.makedirs(args.browser_dir)

        config = parse_pheno_db_config(args)
        prep = PrepareVariables(config)
        prep.build_pedigree(args.pedigree)
        prep.build_variables(args.instruments, args.data_dictionary)

        build_pheno_browser(
            args.pheno_db_filename, args.pheno_name,
            args.browser_dir,
            args.regression
        )

        pheno_conf_path = os.path.join(
            pheno_db_dir,
            '{}.conf'.format(args.pheno_name)
        )

        with open(pheno_conf_path, 'w') as pheno_conf_file:
            generate_pheno_db_config(args).write(pheno_conf_file)

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
