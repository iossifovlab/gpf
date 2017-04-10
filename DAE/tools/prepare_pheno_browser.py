#!/usr/bin/env python
'''
Created on Apr 10, 2017

@author: lubo
'''
import sys
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pheno_browser.prepare_data import PreparePhenoBrowserBase
import traceback

DEBUG = 0
TESTRUN = 0
PROFILE = 0


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


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
            "-p", "--pheno_db",
            dest="pheno_db",
            help="phenotype DB to process",
            metavar="pheno_db")

        parser.add_argument(
            '-o', '--output',
            dest='output_dir',
            help='ouput directory',
            metavar='output_dir')
        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        output_dir = args.output_dir
        pheno_db = args.pheno_db

        if verbose > 0:
            print("Verbose mode on")

        if not pheno_db:
            raise CLIError(
                "pheno DB should be specified")

        if not output_dir:
            raise CLIError(
                "output directory should be specified")

        prep = PreparePhenoBrowserBase(pheno_db, output_dir)
        prep.run()

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception, e:
        traceback.print_exc()

        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'pheno_prepare_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
