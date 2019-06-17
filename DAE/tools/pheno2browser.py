#!/usr/bin/env python
# encoding: utf-8
'''
pheno2browser -- prepares a DAE pheno browser data

'''
from __future__ import print_function, unicode_literals, absolute_import

from future import standard_library; standard_library.install_aliases()  # noqa
from builtins import str

import sys
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import traceback
from pheno import pheno_db
from pheno.pheno_regression import PhenoRegressions
from pheno_browser.prepare_data import PreparePhenoBrowserBase
import hashlib


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def hashsum(filename, hasher, blocksize=65536):
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), b''):
            hasher.update(block)
    return hasher.hexdigest()


def md5sum(filename, blocksize=65536):
    return hashsum(filename, hashlib.md5(), blocksize)


def sha256sum(filename, blocksize=65536):
    return hashsum(filename, hashlib.sha256(), blocksize)


def calc_dbfile_hashsum(dbfilename):
    assert os.path.exists(dbfilename)

    base, _ext = os.path.splitext(dbfilename)
    hashfilename = '{}.hash'.format(base)
    if not os.path.exists(hashfilename):
        hashsum = sha256sum(dbfilename)
        with open(hashfilename, 'w') as f:
            f.write(hashsum)
    else:
        dbtime = os.path.getmtime(dbfilename)
        hashtime = os.path.getmtime(hashfilename)
        if hashtime >= dbtime:
            with open(hashfilename, 'r') as f:
                hashsum = f.read().strip()
        else:
            hashsum = sha256sum(dbfilename)
            with open(hashfilename, 'w') as f:
                f.write(hashsum)
    return hashsum


def build_pheno_browser(dbfile, pheno_name, output_dir, regression_conf_path):
    phenodb = pheno_db.PhenoDB(dbfile=dbfile)
    phenodb.load()

    pheno_regressions = PhenoRegressions(regression_conf_path)

    prep = PreparePhenoBrowserBase(pheno_name, phenodb,
                                   output_dir, pheno_regressions)
    prep.run()

    hashsum = calc_dbfile_hashsum(dbfile)
    hashfile = os.path.join(
        output_dir,
        '{}.hash'.format(pheno_name))
    with open(hashfile, 'w') as f:
        f.write(hashsum)


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

USAGE
''' % (program_shortdesc, )

    try:
        # Setup argument parser
        parser = ArgumentParser(
            description=program_license,
            formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument(
            "-v", "--verbose", dest="verbose",
            action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument(
            "-d", "--dbfile",
            dest="dbfile",
            help="pheno db file anme",
            metavar="path"
        )
        parser.add_argument(
            "-p", "--pheno",
            dest="pheno_name",
            help="pheno name"
        )
        parser.add_argument(
            '-o', '--output',
            dest='output',
            help='output base dir',
            metavar='path')

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
            '--regression',
            help=("path to a regression configuration file"),
            type=str
        )

        # Process arguments
        args = parser.parse_args()

        if not args.output or not os.path.exists(args.output):
            raise CLIError(
                "output directory should be specified and empty"
            )

        if not args.pheno_name:
            raise CLIError(
                "pheno name must be specified")
        if not args.dbfile or not os.path.exists(args.dbfile):
            raise CLIError(
                "pheno db file name must be specified")

        build_pheno_browser(
            args.dbfile, args.pheno_name, args.output, args.regression)

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        traceback.print_exc()
        print()
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())
