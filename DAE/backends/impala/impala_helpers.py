import os
from impala import dbapi


class ImpalaHelpers(object):

    @staticmethod
    def get_impala(impala_host=None, impala_port=None):
        if impala_host is None:
            impala_host = "127.0.0.1"
        impala_host = os.getenv("DAE_IMPALA_HOST", impala_host)
        if impala_port is None:
            impala_port = 21050
        impala_port = int(os.getenv("DAE_IMPALA_PORT", impala_port))

        impala_connection = dbapi.connect(
            host=impala_host,
            port=impala_port)

        return impala_connection

    def __init__(
            self, impala_host=None, impala_port=None, impala_connection=None):
        if impala_connection is None:
            impala_connection = self.get_impala(impala_host, impala_port)
        self.connection = impala_connection

    def import_variants(self, config):
        print("importing variants into impala:", config)

        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS {db}
            """.format(db=config.db))
            self.import_pedigree_file(
                cursor, config.db, config.tables.pedigree,
                config.files.pedigree)
            self.import_variant_files(
                cursor, config.db, config.tables.variant,
                [config.files.variant]
            )

    def import_pedigree_file(self, cursor, dbname, table_name, pedigree_file):
        cursor.execute("""
            DROP TABLE IF EXISTS {db}.{table_name}
        """.format(db=dbname, table_name=table_name))

        cursor.execute("""
            CREATE TABLE {db}.{pedigree} LIKE PARQUET '{pedigree_file}'
            STORED AS PARQUET
        """.format(
                db=dbname, pedigree_file=pedigree_file,
                pedigree=table_name))
        cursor.execute("""
            LOAD DATA INPATH '{pedigree_file}' INTO TABLE {db}.{pedigree}
        """.format(
                db=dbname, pedigree_file=pedigree_file,
                pedigree=table_name))

    def import_variant_files(
            self, cursor, dbname, table_name, variant_files):

        cursor.execute("""
            DROP TABLE IF EXISTS {db}.{table_name}
        """.format(db=dbname, table_name=table_name))

        cursor.execute("""
            CREATE TABLE {db}.{variant} LIKE PARQUET '{variant_file}'
            STORED AS PARQUET
        """.format(
            db=dbname, variant_file=variant_files[0],
            variant=table_name))

        for variant_file in variant_files:
            cursor.execute("""
                LOAD DATA INPATH '{variant_file}'
                INTO TABLE {db}.{variant}
            """.format(
                db=dbname, variant_file=variant_file,
                variant=table_name))

    def check_database(self, dbname):
        with self.connection.cursor() as cursor:
            q = """
                SHOW DATABASES
            """

            cursor.execute(q)
            for row in cursor:
                if row[0] == dbname:
                    return True
        return False

    def check_table(self, dbname, tablename):
        with self.connection.cursor() as cursor:
            q = """
                SHOW TABLES IN {db}
            """.format(db=dbname)

            cursor.execute(q)
            for row in cursor:
                if row[0] == tablename:
                    return True
        return False

    def create_database(self, dbname):
        with self.connection.cursor() as cursor:
            q = """
                CREATE DATABASE IF NOT EXISTS {db}
            """.format(db=dbname)

            cursor.execute(q)

    def drop_database(self, dbname):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                DROP DATABASE IF EXISTS {db} CASCADE
            """.format(db=dbname))
