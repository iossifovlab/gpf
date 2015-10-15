#!/usr/local/bin/python2.7
# encoding: utf-8
'''
myisam_transmitted_import -- import transmitted variants into MySQL

myisam_transmitted_import is a tool to import transmitted variants SQL
tables into MySQL.

@author:     lubo
@contact:    lchorbadjiev@setelis.com
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from DAE import vDB

import MySQLdb as mdb

__all__ = []
__version__ = 0.1
__date__ = '2015-10-15'
__updated__ = '2015-10-15'

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


class Tools(object):

    def __init__(self, study_name):
        self.study = vDB.get_study(study_name)
        self.connection = None

    def get_sql_family_filename(self):
        study = self.study
        family_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.sql.family')
        return family_filename

    def get_sql_gene_effect_filename(self):
        study = self.study
        gene_effect_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.sql.gene_effect')
        return gene_effect_filename

    def get_sql_summary_filename(self):
        study = self.study
        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.sql.summary')
        return summary_filename

    def get_sql_files(self):
        study = self.study
        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.sql.summary')
        gene_effect_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.sql.gene_effect')
        family_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.sql.family')

        return family_filename, gene_effect_filename, summary_filename

    def get_db_conf(self):
        study = self.study
        user = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.mysql.user')
        db = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.mysql.db')
        password = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.mysql.pass')
        host = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.mysql.host')
        return host, user, password, db

    def connect(self):
        (host, user, password, db) = self.get_db_conf()
        if not self.connection:
            self.connection = mdb.connect(
                host, user, password, db)
        return self.connection

    def drop_all_tables(self):
        statement = "DROP TABLE IF EXISTS %s"
        data = [('transmitted_familyvariant',),
                ('transmitted_geneeffectvariant',),
                ('transmitted_summaryvariant',)]
        for table in data:
            connection = self.connect()
            cursor = connection.cursor()
            cursor.execute(statement % table)
            cursor.close()

    def _import_sql_file(self, family_filename):
        host, user, password, db = self.get_db_conf()
        params = {
            'filename': family_filename,
            'host': host,
            'user': user,
            'password': password,
            'db': db}
        command = "gunzip -c %(filename)s | "\
            "mysql -h%(host)s -u%(user)s -p%(password)s %(db)s" % params
        print "executing command: %s" % command
        os.system(command)

    def import_family_variants(self):
        family_filename = self.get_sql_family_filename()
        self._import_sql_file(family_filename)

    def import_gene_effect_variants(self):
        gene_effect_filename = self.get_sql_gene_effect_filename()
        self._import_sql_file(gene_effect_filename)

    def import_summary_variants(self):
        summary_filename = self.get_sql_summary_filename()
        self._import_sql_file(summary_filename)


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version,
                                                     program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_desc = '''%s
%s
USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(
            description=program_desc,
            formatter_class=RawDescriptionHelpFormatter)

        parser.add_argument(
            '-V', '--version',
            action='version', version=program_version_message)

        parser.add_argument(
            dest="study",
            help="study name to process "
            "[default: %(default)s]")

        # Process arguments
        args = parser.parse_args()

        study_name = args.study
        tools = Tools(study_name)

        family_filename, gene_effect_filename, summary_filename = \
            tools.get_sql_files()

        print("Working with sql files:")
        print(" - summary: %s" % summary_filename)
        print(" - effect:  %s" % gene_effect_filename)
        print(" - family:  %s" % family_filename)

        tools.drop_all_tables()
        tools.import_family_variants()
        tools.import_gene_effect_variants()
        tools.import_summary_variants()

        return 0
    except KeyboardInterrupt:
        # handle keyboard interrupt
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    sys.exit(main())
