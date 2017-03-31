#!/usr/bin/env python
# encoding: utf-8
'''
pheno2DAE -- prepares a DAE pheno DB cache

'''

import sys
import os
import pandas as pd
import numpy as np

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import traceback
from pheno.models import PersonManager
from collections import Counter
from pheno.prepare.base_variables import BaseVariables
from pheno.utils.configuration import PhenoConfig
from pheno.prepare.base_meta_variables import BaseMetaVariables
from pheno.pheno_db import PhenoDB
import ConfigParser
from pprint import pprint

__all__ = []
__version__ = 0.1
__date__ = '2017-03-20'
__updated__ = '2017-03-20'

DEBUG = 0
TESTRUN = 0
PROFILE = 0


def config_pheno_db(output):
    config = ConfigParser.SafeConfigParser()
    config.add_section('cache_dir')
    config.set('cache_dir', 'dir', '.')
    config.add_section('output')
    config.set('output', 'cache_file', output)

    config.add_section('continuous')
    config.set('continuous', 'min_individuals', '20')
    config.set('continuous', 'min_rank', '15')

    config.add_section('ordinal')
    config.set('ordinal', 'min_individuals', '20')
    config.set('ordinal', 'min_rank', '5')
    config.set('ordinal', 'max_rank', '17')

    config.add_section('categorical')
    config.set('categorical', 'min_individuals', '20')
    config.set('categorical', 'min_rank', '2')
    config.set('categorical', 'max_rank', '7')

    return config


class PrepareIndividuals(PhenoConfig):

    def __init__(self, config, *args, **kwargs):
        super(PrepareIndividuals, self).__init__(
            pheno_db='output', config=config, *args, **kwargs)

    def load_persons(self, families_file):
        assert os.path.isfile(families_file)

        df = pd.read_csv(families_file, sep='\t')
        assert 'familyId' in df.columns
        assert 'personId' in df.columns

        columns = list(df.columns)
        columns[columns.index('familyId')] = 'family_id'
        columns[columns.index('personId')] = 'person_id'
        df.columns = columns
        df['role_order'] = np.arange(len(df))
        df['role_id'] = df.role

        return df

    def prepare(self, families_file):
        persons_df = self.load_persons(families_file)
        with PersonManager(pheno_db=self.pheno_db, config=self.config) as pm:
            pm.drop_tables()
            pm.create_tables()

            pm.save_df(persons_df)


class PrepareVariables(PhenoConfig, BaseVariables):

    def __init__(self, config, *args, **kwargs):
        super(PrepareVariables, self).__init__(
            pheno_db='output', config=config, *args, **kwargs)

    def _clear_duplicate_measurements(self, df):
        counter = Counter(df.person_id)
        to_fix = [k for k, v in counter.items() if v > 1]
        to_delete = []
        for person_id in to_fix:
            print("fixing measurements for {}".format(person_id))
            pdf = df[df.person_id == person_id]
            keep = pdf.age.idxmax()
            d = pdf[pdf.index != keep]
            to_delete.extend(d.index.values)

        df.drop(to_delete, inplace=True)

    def load_instrument(self, filename, dtype=None):
        assert os.path.isfile(filename)
        print("processing table: {}".format(filename))

        df = pd.read_csv(filename, low_memory=False, sep=',',
                         na_values=[' '], dtype=dtype)
        columns = [c for c in df.columns]
        columns[0] = 'person_id'
        df.columns = columns
        self._clear_duplicate_measurements(df)
        return df

    def prepare(self, instruments_directory):
        self._create_variable_table()
        self._create_value_tables()

        persons = self.load_persons_df()

        all_filenames = [
            os.path.join(instruments_directory, f)
            for f in os.listdir(instruments_directory)
            if os.path.isfile(os.path.join(instruments_directory, f))]
        print(all_filenames)
        for filename in all_filenames:
            basename = os.path.basename(filename)
            instrument_name, ext = os.path.splitext(basename)
            print(basename)
            print(instrument_name, ext)
            if ext != '.csv':
                continue
            instrument_df = self.load_instrument(filename)

            df = instrument_df.join(persons, on='person_id', rsuffix="_person")

            for measure_name in df.columns[1:len(instrument_df.columns)]:
                mdf = df[['person_id', measure_name,
                          'family_id', 'person_role']]
                self._build_variable(instrument_name, measure_name,
                                     mdf.dropna())


class PrepareMetaVariables(PhenoConfig, BaseMetaVariables):

    def __init__(self, config, *args, **kwargs):
        super(PrepareMetaVariables, self).__init__(
            pheno_db='output', config=config, *args, **kwargs)
        self.phdb = PhenoDB(self.pheno_db, config=config)
        self.phdb.load()


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

        prep_inidividuals = PrepareIndividuals(config)
        prep_inidividuals.prepare(families_filename)

        prep_variables = PrepareVariables(config)
        prep_variables.prepare(instruments_directory)

        prep_meta = PrepareMetaVariables(config)
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
