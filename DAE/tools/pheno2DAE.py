#!/usr/bin/env python
# encoding: utf-8
'''
pheno2DAE -- prepares a DAE pheno DB cache

'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import traceback
from pprint import pprint
from pheno.prepare.nuc_ped_prepare import NucPedPrepareIndividuals,\
    NucPedPrepareVariables, NucPedPrepareMetaVariables
from pheno.common import config_pheno_db

__all__ = []
__version__ = 0.1
__date__ = '2017-03-20'
__updated__ = '2017-03-20'

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
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (
        program_version, program_build_date)
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
            '-V', '--version', action='version',
            version=program_version_message)
        parser.add_argument(
            "-i", "--instruments",
            dest="instruments",
            help="directory where all instruments are located",
            metavar="path")
        parser.add_argument(
            "-f", "--families",
            dest="families",
            help="file where families description are located",
            metavar="path")

        parser.add_argument(
            '-o', '--output',
            dest='output',
            help='ouput file',
            metavar='filename')
        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        instruments_directory = args.instruments
        families_filename = args.families
        output = args.output

        if verbose > 0:
            print("Verbose mode on")

        if not families_filename or not instruments_directory:
            raise CLIError(
                "families file and instruments directory must be specified")
        if not output:
            raise CLIError(
                "output filename should be specified")

        config = config_pheno_db(output)
        pprint(config)

        prep_individuals = NucPedPrepareIndividuals(config)
        prep_individuals.prepare(families_filename)

        prep_variables = NucPedPrepareVariables(config)
        prep_variables.prepare(prep_individuals, instruments_directory)

        prep_meta = NucPedPrepareMetaVariables(config)
        prep_meta.prepare()

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
