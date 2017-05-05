#!/usr/bin/env python
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

    def __init__(self, args):
        self.study_name = args.study
        self.args = args

        self.connection = None

    def get_study_conf(self):
        if self.study_name is None:
            return {}
        study = vDB.get_study(self.study_name)
        user = study.vdb._config.get(study._configSection,
                                     'transmittedVariants.user')
        db = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.db')
        password = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.pass')
        host = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.host')
        port = None
        if study.vdb._config.has_option(
                study._configSection,
                'transmittedVariants.port'):
            port = study.vdb._config.get(
                study._configSection,
                'transmittedVariants.port')
        if port is None:
            port = 3306
        else:
            port = int(port)
        res = {
            'host': host,
            'port': port,
            'user': user,
            'passwd': password,
            'db': db}
        return res

    def check_db_params(self, params):
        for key in ['host', 'port', 'user', 'passwd', 'db']:
            assert params.get(key, None), \
                "DB connection parameter '{}' missing".format(key)

    def get_db_conf(self):
        res = self.get_study_conf()

        args_db_conf = get_db_args(self.args)
        for k, v in args_db_conf.items():
            if v is not None:
                res[k] = v

        self.check_db_params(res)
        return res

    def connect(self):
        if not self.connection:
            db_conf = self.get_db_conf()
            self.connection = mdb.connect(
                **db_conf)
        return self.connection

    def drop_all_tables(self):
        statement = "DROP TABLE IF EXISTS %s"
        data = [
            ('transmitted_familyvariant',),
            ('transmitted_geneeffectvariant',),
            ('transmitted_summaryvariant',)]
        for table in data:
            connection = self.connect()
            cursor = connection.cursor()
            cursor.execute(statement % table)
            cursor.close()

    def _import_sql_file(self, filename):
        assert os.path.exists(filename)
        params = self.get_db_conf()
        params['filename'] = filename
        command = "gunzip -c %(filename)s | "\
            "mysql -h%(host)s -P%(port)s -u%(user)s -p%(passwd)s %(db)s" % \
            params
        print "executing command: %s" % command
        os.system(command)

    def import_family_variants(self, family_filename):
        self._import_sql_file(family_filename)

    def import_gene_effect_variants(self, gene_effect_filename):
        self._import_sql_file(gene_effect_filename)

    def import_summary_variants(self, summary_filename):
        self._import_sql_file(summary_filename)


def get_db_args(args):
    user = args.user
    db = args.database
    password = args.password
    host = args.host
    port = args.port
    if port is None:
        port = None
    else:
        port = int(port)

    return {
        'host': host,
        'port': port,
        'user': user,
        'passwd': password,
        'db': db
    }


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
            '-s', '--summary',
            dest='summary_filename',
            default='sql_summary_variants_myisam.sql.gz')

        parser.add_argument(
            '-f', '--family',
            dest='family_filename',
            default='sql_family_variants_myisam.sql.gz')

        parser.add_argument(
            '-e', '--gene_effect',
            dest='gene_effect_filename',
            default='sql_gene_effect_variants_myisam.sql.gz')

        parser.add_argument(
            '-H', '--host',
            dest="host",
            help="MySQL host",
            default=None)

        parser.add_argument(
            '-P', '--port',
            dest="port",
            help="MySQL port",
            default=None)

        parser.add_argument(
            '-p', '--password',
            dest="password",
            help="MySQL password",
            default=None)

        parser.add_argument(
            '-u', '--user',
            dest='user',
            help='MySQL user',
            default=None)

        parser.add_argument(
            '-D', '--database',
            dest='database',
            help='MySQL database',
            default=None)

        parser.add_argument(
            '-S', '--study',
            dest="study",
            help="study name to process "
            "[default: %(default)s]")

        # Process arguments
        args = parser.parse_args()

        tools = Tools(args)

        family_filename = args.family_filename
        gene_effect_filename = args.gene_effect_filename
        summary_filename = args.summary_filename

        print("Working with sql files:")
        print(" - summary: %s" % summary_filename)
        print(" - effect:  %s" % gene_effect_filename)
        print(" - family:  %s" % family_filename)

        print("db conf: %s" % get_db_args(args))
        print("tool db conf: %s" % tools.get_db_conf())

        assert tools.get_db_conf()['port'] == 3309

        tools.drop_all_tables()
        tools.import_family_variants(family_filename)
        tools.import_gene_effect_variants(gene_effect_filename)
        tools.import_summary_variants(summary_filename)

        return 0
    except KeyboardInterrupt:
        # handle keyboard interrupt
        return 0
    except Exception, e:
        import traceback
        traceback.print_exc()

        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())
