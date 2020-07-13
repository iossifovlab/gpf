import os
import sys
import itertools

from contextlib import closing

from impala import dbapi
from sqlalchemy.pool import QueuePool


class ImpalaHelpers(object):

    def __init__(self, impala_hosts, impala_port=21050, pool_size=10):

        if os.environ.get("DAE_IMPALA_HOST", None) is not None:
            impala_host = os.environ.get("DAE_IMPALA_HOST", None)
            print("impala host overwritten:", impala_host)
            if impala_host is not None:
                impala_hosts = [impala_host]
        if impala_hosts is None:
            impala_hosts = []

        host_generator = itertools.cycle(impala_hosts)

        def getconn():
            impala_host = next(host_generator)
            return dbapi.connect(host=impala_host, port=impala_port)

        print(
            f"Creating impala pool with {pool_size} connections",
            file=sys.stderr)

        self._connection_pool = QueuePool(
            getconn, pool_size=pool_size, reset_on_return=False)

    def connection(self):
        return self._connection_pool.connect()

    def import_variants(
            self,
            db,
            variant_table,
            pedigree_table,
            variant_hdfs_path,
            pedigree_hdfs_path):
        assert db is not None

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE DATABASE IF NOT EXISTS {db}
                    """)

                self.import_files(
                    cursor, db, pedigree_table, pedigree_hdfs_path)
                if variant_hdfs_path:
                    self.import_files(
                        cursor, db, variant_table, variant_hdfs_path)

    def import_files(self, cursor, db, table_name, import_files):

        cursor.execute(
            f"""
            DROP TABLE IF EXISTS {db}.{table_name}
            """)

        cursor.execute(
            f"""
            CREATE TABLE {db}.{table_name}
            LIKE PARQUET '{import_files[0]}'
            STORED AS PARQUET
            """)

        for import_file in import_files:
            cursor.execute(
                f"""
                LOAD DATA INPATH '{import_file}'
                INTO TABLE {db}.{table_name}
                """)

    def import_single_file(self, cursor, db, table, import_file):

        cursor.execute(
            f"""
            DROP TABLE IF EXISTS {db}.{table}
            """)

        dirname = os.path.dirname(import_file)
        statement = f"""
            CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{import_file}'
            STORED AS PARQUET LOCATION '{dirname}'
        """
        cursor.execute(statement)
        cursor.execute(f"REFRESH {db}.{table}")

    def add_partition_properties(
            self, cursor, db, table, partition_description):

        chromosomes = ", ".join(partition_description.chromosomes)
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_region_bin_chromosomes' = "
            f"'{chromosomes}'"
            ")"
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_region_bin_region_length' = "
            f"'{partition_description.region_length}'"
            ")"
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_family_bin_family_bin_size' = "
            f"'{partition_description.family_bin_size}'"
            ")"
        )
        coding_effect_types = ",".join(
            partition_description.coding_effect_types
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_coding_bin_coding_effect_types' = "
            f"'{coding_effect_types}'"
            ")"
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_frequency_bin_rare_boundary' = "
            f"'{partition_description.rare_boundary}'"
            ")"
        )

    def create_dataset_table(
            self, cursor, db, table,
            sample_file,
            pd):

        cursor.execute(
            """
            DROP TABLE IF EXISTS {db}.{table}
        """.format(
                db=db, table=table
            )
        )

        print("pd.has_partitions():", pd, pd.has_partitions())

        hdfs_dir = pd.variants_filename_basedir(sample_file)
        if not pd.has_partitions():
            statement = f"""
                CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{sample_file}'
                STORED AS PARQUET LOCATION '{hdfs_dir}'
            """
        else:
            partitions = pd.build_impala_partitions()
            statement = f"""
                CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{sample_file}'
                PARTITIONED BY ({partitions})
                STORED AS PARQUET LOCATION '{hdfs_dir}'
            """

        cursor.execute(statement)

        if pd.has_partitions():
            cursor.execute(
                f"""
                ALTER TABLE {db}.{table} RECOVER PARTITIONS
            """
            )
        cursor.execute(
            f"""
            REFRESH {db}.{table}
        """
        )

    def import_dataset_into_db(
            self,
            db,
            pedigree_table,
            variants_table,
            pedigree_hdfs_file,
            variants_hdfs_file,
            partition_description):

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE DATABASE IF NOT EXISTS {db}
                """
                )
                self.import_single_file(
                    cursor, db, pedigree_table, pedigree_hdfs_file)

                self.create_dataset_table(
                    cursor,
                    db,
                    variants_table,
                    variants_hdfs_file,
                    partition_description
                )
                if partition_description.has_partitions():
                    self.add_partition_properties(
                        cursor, db, variants_table, partition_description
                    )

    def check_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    SHOW DATABASES
                """

                cursor.execute(q)
                for row in cursor:
                    if row[0] == dbname:
                        return True
        return False

    def check_table(self, dbname, tablename):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = f"""
                    SHOW TABLES IN {dbname}
                """

                cursor.execute(q)
                for row in cursor:
                    if row[0] == tablename:
                        return True
        return False

    def drop_table(self, dbname, tablename):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = f"""
                    DROP TABLE IF EXISTS {dbname}.{tablename}
                """
                cursor.execute(q)

    def create_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    CREATE DATABASE IF NOT EXISTS {db}
                """.format(
                    db=dbname
                )

                cursor.execute(q)

    def drop_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DROP DATABASE IF EXISTS {db} CASCADE
                """.format(
                        db=dbname
                    )
                )
