#!/usr/bin/env python
# encoding: utf-8
"""
pheno2browser -- prepares a DAE pheno browser data

"""
import sys
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import traceback

from dae.pheno import pheno_db
from dae.pheno.prepare_data import PreparePhenoBrowserBase
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema

from dae.utils.filehash import sha256sum


class CLIError(Exception):
    """Generic exception to raise and log different fatal errors."""

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def calc_dbfile_hashsum(dbfilename):
    assert os.path.exists(dbfilename)

    base, _ext = os.path.splitext(dbfilename)
    hashfilename = "{}.hash".format(base)
    if not os.path.exists(hashfilename):
        hash_sum = sha256sum(dbfilename)
        with open(hashfilename, "w") as f:
            f.write(hash_sum)
    else:
        dbtime = os.path.getmtime(dbfilename)
        hashtime = os.path.getmtime(hashfilename)
        if hashtime >= dbtime:
            with open(hashfilename, "r") as f:
                hash_sum = f.read().strip()
        else:
            hash_sum = sha256sum(dbfilename)
            with open(hashfilename, "w") as f:
                f.write(hash_sum)
    return hash_sum


def build_pheno_browser(
    dbfile, pheno_name, output_dir, pheno_regressions=None
):
    phenodb = pheno_db.PhenotypeStudy(pheno_name, dbfile=dbfile)

    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    prep = PreparePhenoBrowserBase(
        pheno_name, phenodb, output_dir, pheno_regressions, images_dir)
    prep.run()

    # hash_sum = calc_dbfile_hashsum(dbfile)
    # hashfile = os.path.join(
    #     output_dir,
    #     '{}.hash'.format(pheno_name))
    # with open(hashfile, 'w') as f:
    #     f.write(hash_sum)


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
        # Setup argument parser
        parser = ArgumentParser(
            description=program_license,
            formatter_class=RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="count",
            help="set verbosity level [default: %(default)s]",
        )
        parser.add_argument(
            "-d",
            "--dbfile",
            dest="dbfile",
            help="pheno db file anme",
            metavar="path",
        )
        parser.add_argument(
            "-p", "--pheno", dest="pheno_name", help="pheno name"
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="output",
            help="output base dir",
            metavar="path",
        )

        parser.add_argument(
            "--regression",
            help=("path to a regression configuration file"),
            type=str,
        )

        # Process arguments
        args = parser.parse_args()

        if not args.output or not os.path.exists(args.output):
            raise CLIError("output directory should be specified and empty")

        if not args.pheno_name:
            raise CLIError("pheno name must be specified")
        if not args.dbfile or not os.path.exists(args.dbfile):
            raise CLIError("pheno db file name must be specified")

        regressions = (
            GPFConfigParser.load_config(
                args.regression, regression_conf_schema
            )
            if args.regression
            else None
        )

        build_pheno_browser(
            args.dbfile, args.pheno_name, args.output, regressions
        )

        return 0
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        traceback.print_exc()
        print()
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())
