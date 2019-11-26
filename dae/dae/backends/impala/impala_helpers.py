from impala import dbapi


class ImpalaHelpers(object):

    @staticmethod
    def create_impala_connection(impala_host, impala_port):
        assert impala_host
        assert impala_port

        impala_connection = dbapi.connect(
            host=impala_host,
            port=impala_port)

        return impala_connection

    def __init__(
            self, impala_host=None, impala_port=None, impala_connection=None):
        if impala_connection is None:
            assert impala_host
            assert impala_port

            impala_connection = self.create_impala_connection(
                impala_host, impala_port
            )
        self.connection = impala_connection

    def import_variants(
            self, db,
            variant_table, pedigree_table,
            variant_hdfs_path, pedigree_hdfs_path):

        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS {db}
            """.format(db=db))
            self.import_files(
                cursor, db, pedigree_table,
                pedigree_hdfs_path)
            self.import_files(
                cursor, db, variant_table,
                variant_hdfs_path)

    def import_files(self, cursor, dbname, table_name, import_files):

        cursor.execute("""
            DROP TABLE IF EXISTS {db}.{table_name}
        """.format(db=dbname, table_name=table_name))

        cursor.execute("""
            CREATE TABLE {db}.{table_name} LIKE PARQUET '{import_file}'
            STORED AS PARQUET
        """.format(
            db=dbname, import_file=import_files[0],
            table_name=table_name))

        for import_file in import_files:
            cursor.execute("""
                LOAD DATA INPATH '{import_file}'
                INTO TABLE {db}.{table_name}
            """.format(
                db=dbname, import_file=import_file,
                table_name=table_name))

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
            q = f"""
                SHOW TABLES IN {dbname}
            """

            cursor.execute(q)
            for row in cursor:
                if row[0] == tablename:
                    return True
        return False

    def drop_table(self, dbname, tablename):
        with self.connection.cursor() as cursor:
            q = f"""
                DROP TABLE IF EXISTS {dbname}.{tablename}
            """
            cursor.execute(q)

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
