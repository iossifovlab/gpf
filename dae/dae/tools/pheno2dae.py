#!/usr/bin/env python
# encoding: utf-8
"""
pheno2dae -- prepares a DAE pheno DB cache

"""
import sys
import os
import logging

from argparse import ArgumentParser

# from argparse import ArgumentDefaultsHelpFormatter
import traceback
from dae.pheno.common import (
    dump_config,
    check_phenotype_data_config,
    default_config,
)
from dae.pheno.prepare.pheno_prepare import PrepareVariables


logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Generic exception to raise and log different fatal errors."""

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def parse_config(args):
    config = default_config()
    config.verbose = args.verbose
    config.instruments.dir = args.instruments
    config.pedigree = args.pedigree
    config.db.filename = args.output

    skip_columns = set([])
    if args.skip_file:
        assert os.path.exists(args.skip_file)
        with open(args.skip_file, "r") as infile:
            columns = infile.readlines()
            columns = [col.strip() for col in columns]
            skip_columns = skip_columns | set(columns)
    if args.skip_columns:
        columns = set([col for col in args.skip_columns.split(",")])
        skip_columns = skip_columns | columns

    config.skip.measures = skip_columns
    if args.composite_fids:
        config.family.composite_key = args.composite_fids

    if args.role:
        config.person.role.type = args.role
    assert config.person.role.type in set(["column", "guess"])

    if args.role_mapping:
        config.person.role.mapping = args.role_mapping
    assert config.person.role.mapping in set(["SPARK", "SSC", "INTERNAL"])

    if args.person_column:
        config.person.column = args.person_column

    if args.min_individuals is not None and args.min_individuals >= 0:
        config.classification.min_individuals = args.min_individuals

    if args.categorical is not None and args.categorical >= 0:
        config.classification.categorical.min_rank = args.categorical

    if args.ordinal is not None and args.ordinal >= 0:
        config.classification.ordinal.min_rank = args.ordinal

    if args.continuous is not None and args.continuous >= 0:
        config.classification.continuous.min_rank = args.continuous

    if args.tab_separated:
        config.instruments.tab_separated = True

    if args.report_only:
        config.db.filename = "memory"
        config.report_only = args.report_only

    if args.parallel:
        config.parallel = args.parallel

    return config


def main(argv=None):  # IGNORE:C0111
    """Command line options."""

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_shortdesc = __import__("__main__").__doc__.split("\n")[1]
    program_license = """%s

USAGE
""" % (
        program_shortdesc,
    )

    try:
        defaults = default_config()

        # Setup argument parser
        parser = ArgumentParser(description=program_license)
        # formatter_class=RawDescriptionHelpFormatter
        # formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "-V",
            "--verbose",
            dest="verbose",
            action="count",
            help="set verbosity level",
            default=0
        )
        parser.add_argument(
            "-i",
            "--instruments",
            dest="instruments",
            help="directory where all instruments are located",
            metavar="path",
        )
        parser.add_argument(
            "-p",
            "--pedigree",
            dest="pedigree",
            help="pedigree file where families descriptions are located",
            metavar="path",
        )
        parser.add_argument(
            "-d",
            "--description",
            help="standardized tsv file that contains measure descriptions",
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="output",
            help="output file",
            metavar="filename",
        )
        parser.add_argument(
            "-C",
            "--continuous",
            type=int,
            dest="continuous",
            default=defaults["classification"]["continuous"]["min_rank"],
            help="minimal count of unique values for a measure to be "
            "classified as continuous (default: %(default)s)",
        )
        parser.add_argument(
            "-O",
            "--ordinal",
            type=int,
            dest="ordinal",
            default=defaults["classification"]["ordinal"]["min_rank"],
            help="minimal count of unique values for a measure to be "
            "classified as ordinal (default: %(default)s)",
        )

        parser.add_argument(
            "-A",
            "--categorical",
            type=int,
            dest="categorical",
            default=defaults["classification"]["categorical"]["min_rank"],
            help="minimal count of unique values for a measure to be "
            "classified as categorical (default: %(default)s)",
        )

        parser.add_argument(
            "-I",
            "--min-individuals",
            type=int,
            dest="min_individuals",
            default=defaults["classification"]["min_individuals"],
            help="minimal number of individuals for a measure to be "
            "considered for classification (default: %(default)s)",
        )

        parser.add_argument(
            "-S",
            "--skip-columns",
            type=str,
            dest="skip_columns",
            help="comma separated list of instruments columns to skip",
        )

        parser.add_argument(
            "--skip-file",
            type=str,
            dest="skip_file",
            help="file with list of instruments columns to skip",
        )

        parser.add_argument(
            "--composite-fids",
            action="store_true",
            dest="composite_fids",
            help="builds composite family IDs from parents' IDs"
            " (default: %(default)s)",
        )

        parser.add_argument(
            "-r",
            "--role",
            dest="role",
            default=defaults["person"]["role"]["type"],
            help='sets role handling; available choices: "column", "guess"'
            " (default: %(default)s)",
        )

        parser.add_argument(
            "--role-mapping",
            dest="role_mapping",
            default=defaults["person"]["role"]["mapping"],
            help="sets role column mapping rules; "
            'available choices "SPARK", "SSC", "INTERNAL"'
            " (default: %(default)s)",
        )

        parser.add_argument(
            "-P",
            "--person-column",
            dest="person_column",
            # default=defaults['person']['role']['column'],
            help="sets name of a column in instrument's files, "
            "containing personId (default: %(default)s)",
        )

        parser.add_argument(
            "-T",
            "--tab-separated",
            dest="tab_separated",
            action="store_true",
            help="instruments file are tab separated"
            " (default: %(default)s)",
        )

        parser.add_argument(
            "--report-only",
            dest="report_only",
            action="store_true",
            help="runs the tool in report only mode (default: %(default)s)",
        )

        parser.add_argument(
            "--parallel",
            type=int,
            dest="parallel",
            default=defaults["parallel"],
            help="size of executors pool to use for processing"
            " (default: %(default)s)",
        )

        # Process arguments
        args = parser.parse_args()

        if args.verbose == 1:
            logging.basicConfig(level=logging.WARNING)
        elif args.verbose == 2:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 3:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.ERROR)

        if not args.output and not args.report_only:
            raise CLIError("output filename should be specified")

        if not args.output:
            args.output = "output.db"

        if not args.pedigree:
            raise CLIError("pedigree file must be specified")
        if not args.instruments:
            raise CLIError("instruments directory should be specified")

        config = parse_config(args)
        dump_config(config)

        if not check_phenotype_data_config(config):
            raise Exception("bad classification boundaries")

        if os.path.exists(args.output):
            raise CLIError("output file already exists")

        prep = PrepareVariables(config)
        prep.build_pedigree(args.pedigree)
        prep.build_variables(args.instruments, args.description)

        return 0
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        traceback.print_exc()

        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
