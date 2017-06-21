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
from pheno.prepare.nuc_ped_prepare import NucPedPrepareIndividuals,\
    NucPedPrepareVariables, NucPedPrepareMetaVariables
from pheno.common import config_pheno_db, adjust_config_pheno_db, dump_config,\
    check_config_pheno_db

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

        parser.add_argument(
            '-C', '--continuous',
            type=int,
            dest='continuous',
            help='minimal count of unique values for a measure to be '
            'classified as continuous (default: 15)')

        parser.add_argument(
            '-O', '--ordinal',
            type=int,
            dest='ordinal',
            help='minimal count of unique values for a measure to be '
            'classified as ordinal (default: 5)')

        parser.add_argument(
            '-A', '--categorical',
            type=int,
            dest='categorical',
            help='minimal count of unique values for a measure to be '
            'classified as categorical (default: 2)')

        parser.add_argument(
            '-I', '--individuals',
            type=int,
            dest='individuals',
            help='minimal number of individuals for a measure to be '
            'considered for classification (default: 20)')

        parser.add_argument(
            '-S', '--skip-columns',
            type=str,
            dest="skip_columns",
            help="comma separated list of instruments columns to skip")

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose
        instruments_directory = args.instruments
        families_filename = args.families
        output = args.output
        skip_columns = args.skip_columns
        if skip_columns:
            skip_columns = set([
                col for col in skip_columns.split(',')
            ])

        if not families_filename:
            raise CLIError(
                "families file must be specified")
        if not output:
            raise CLIError(
                "output filename should be specified")

        config = config_pheno_db(output)
        config = adjust_config_pheno_db(config, args)

        dump_config(config)
        if not check_config_pheno_db(config):
            raise Exception("bad classification boundaries")

        prep_individuals = NucPedPrepareIndividuals(config)
        prep_individuals.prepare(families_filename, verbose)

        prep_variables = NucPedPrepareVariables(config)
        prep_variables.setup(verbose)
        prep_variables.prepare_pedigree_instrument(
            prep_individuals, families_filename, verbose)
        if instruments_directory:
            prep_variables.prepare_instruments(
                prep_individuals, instruments_directory, verbose,
                skip_columns)

        prep_meta = NucPedPrepareMetaVariables(config)
        prep_meta.prepare(verbose)

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
