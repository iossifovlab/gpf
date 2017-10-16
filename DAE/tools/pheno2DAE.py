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
from pheno.common import dump_config,\
    check_config_pheno_db, default_config
from pheno.prepare.ped_prepare import PreparePersons, PrepareVariables,\
    PrepareMetaMeasures


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

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
    config.instruments = args.instruments
    config.pedigree = args.pedigree
    config.db.filename = args.output
    if args.skip_columns:
        skip_columns = set([
            col for col in args.skip_columns.split(',')
        ])
        config.skip.measures = skip_columns
    if args.composite_fids:
        config.family.composite_key = args.composite_fids

    if args.role:
        config.person.role.type = args.role
    assert config.person.role.type in set(['column', 'guess'])

    if args.role_mapping:
        config.person.role.mapping = args.role_mapping
    assert config.person.role.mapping in set(['SPARK', 'SSC', 'INTERNAL'])

    if args.min_individuals is not None and args.min_individuals >= 0:
        config.classification.min_individuals = args.min_individuals

    if args.categorical is not None and args.categorical >= 0:
        config.classification.categorical.min_rank = args.categorical

    if args.ordinal is not None and args.ordinal >= 0:
        config.classification.ordinal.min_rank = args.ordinal

    if args.continuous is not None and args.continuous >= 0:
        config.classification.continuous.min_rank = args.continuous

    return config


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
            "-i", "--instruments",
            dest="instruments",
            help="directory where all instruments are located",
            metavar="path")
        parser.add_argument(
            "-p", "--pedigree",
            dest="pedigree",
            help="pedigree file where families descriptions are located",
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
            '-I', '--min-individuals',
            type=int,
            dest='min_individuals',
            help='minimal number of individuals for a measure to be '
            'considered for classification (default: 20)')

        parser.add_argument(
            '-S', '--skip-columns',
            type=str,
            dest="skip_columns",
            help="comma separated list of instruments columns to skip")

        parser.add_argument(
            '--composite-fids',
            action="store_true",
            dest='composite_fids',
            help="builds composite family IDs from parents' IDs"
        )

        parser.add_argument(
            '-r', '--role',
            dest='role',
            help='sets role handling; available choices "column", "guess"; '
            'default value is "column"'
        )

        parser.add_argument(
            '--role-mapping',
            dest='role_mapping',
            help='sets role column mapping rules; '
            'available choices "SPARK", "SSC", "INTERNAL"; '
            'default value is "INTERNAL"'
        )

        parser.add_argument(
            '-M', '--meta',
            dest='meta',
            help="updates measure meta data only",
            action="store_true"
        )
        # Process arguments
        args = parser.parse_args()

        if not args.output:
            raise CLIError(
                "output filename should be specified")

        if not args.meta:
            if not args.pedigree:
                raise CLIError(
                    "pedigree file must be specified")
            if not args.instruments:
                raise CLIError(
                    "instruments directory should be specified")

        config = parse_config(args)
        dump_config(config)

        if not check_config_pheno_db(config):
            raise Exception("bad classification boundaries")

        if not args.meta:
            prep = PreparePersons(config)
            ped_df = prep.build(args.pedigree)

            prep = PrepareVariables(config, ped_df)
            prep.build(args.instruments)

        prep = PrepareMetaMeasures(config)
        prep.build()

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception, e:
        traceback.print_exc()

        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())
