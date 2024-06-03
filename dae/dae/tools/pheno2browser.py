#!/usr/bin/env python
"""pheno2browser -- prepares a DAE pheno browser data."""
import os
import sys
import traceback
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import regression_conf_schema
from dae.pheno import pheno_data
from dae.pheno.prepare_data import PreparePhenoBrowserBase
from dae.task_graph.cli_tools import TaskGraphCli
from dae.utils.filehash import sha256sum


class CLIError(Exception):
    """Generic exception to raise and log different fatal errors."""

    def __init__(self, msg: str):
        super().__init__(type(self))
        self.msg = f"E: {msg}"

    def __str__(self) -> str:
        return self.msg

    def __unicode__(self) -> str:
        return self.msg


def calc_dbfile_hashsum(dbfilename):
    assert os.path.exists(dbfilename)

    base, _ext = os.path.splitext(dbfilename)
    hashfilename = f"{base}.hash"
    if not os.path.exists(hashfilename):
        hash_sum = sha256sum(dbfilename)
        Path(hashfilename).write_text(hash_sum)
    else:
        dbtime = os.path.getmtime(dbfilename)
        hashtime = os.path.getmtime(hashfilename)
        if hashtime >= dbtime:
            hash_sum = Path(hashfilename).read_text().strip()
        else:
            hash_sum = sha256sum(dbfilename)
            Path(hashfilename).write_text(hash_sum)
    return hash_sum


def build_pheno_browser(
    dbfile, pheno_name, output_dir, pheno_regressions=None, **kwargs,
):
    """Calculate and save pheno browser values to db."""

    phenodb = pheno_data.PhenotypeStudy(
        pheno_name, dbfile=dbfile, read_only=False,
    )

    phenodb.db.create_all_tables()

    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    prep = PreparePhenoBrowserBase(
        pheno_name, phenodb, output_dir, pheno_regressions, images_dir)
    prep.run(**kwargs)


def main(argv=None):
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
            "-p", "--pheno", dest="pheno_name", help="pheno name",
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

        TaskGraphCli.add_arguments(
            parser, use_commands=False,
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
                args.regression, regression_conf_schema,
            )
            if args.regression
            else None
        )

        build_pheno_browser(
            args.dbfile, args.pheno_name, args.output, regressions,
            **vars(args),
        )
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        traceback.print_exc()
        print()
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
