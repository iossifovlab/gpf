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

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE DATABASE IF NOT EXISTS {db}
                """.format(
                        db=db
                    )
                )
                self.import_files(
                    cursor, db, pedigree_table, pedigree_hdfs_path)
                if variant_hdfs_path:
                    self.import_files(
                        cursor, db, variant_table, variant_hdfs_path)

    def import_files(self, cursor, dbname, table_name, import_files):

        cursor.execute(
            """
            DROP TABLE IF EXISTS {db}.{table_name}
        """.format(
                db=dbname, table_name=table_name
            )
        )

        cursor.execute(
            """
            CREATE TABLE {db}.{table_name} LIKE PARQUET '{import_file}'
            STORED AS PARQUET
        """.format(
                db=dbname, import_file=import_files[0], table_name=table_name
            )
        )

        for import_file in import_files:
            cursor.execute(
                """
                LOAD DATA INPATH '{import_file}'
                INTO TABLE {db}.{table_name}
            """.format(
                    db=dbname, import_file=import_file, table_name=table_name
                )
            )

    def add_partition_properties(
        self, cursor, db, table, partition_description
    ):
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
        self, cursor, db, table, hdfs_path, sample_file, partition_description
    ):
        cursor.execute(
            """
            DROP TABLE IF EXISTS {db}.{table}
        """.format(
                db=db, table=table
            )
        )

        partitions = ["region_bin string"]

        if not partition_description.rare_boundary <= 0:
            partitions.append("frequency_bin tinyint")
        if not partition_description.coding_effect_types == []:
            partitions.append("coding_bin tinyint")
        if not partition_description.family_bin_size <= 0:
            partitions.append("family_bin tinyint")

        partitions = ", ".join(partitions)
        cursor.execute(
            f"""
            CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{sample_file}'
            PARTITIONED BY ({partitions})
            STORED AS PARQUET LOCATION '{hdfs_path}'
        """
        )
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
        partition_table,
        pedigree_table,
        partition_description,
        pedigree_hdfs_path,
        dataset_hdfs_path,
        files,
    ):

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE DATABASE IF NOT EXISTS {db}
                """
                )
                sample_file = os.path.join(dataset_hdfs_path, files[0])
                self.create_dataset_table(
                    cursor,
                    db,
                    partition_table,
                    dataset_hdfs_path,
                    sample_file,
                    partition_description,
                )

                self.add_partition_properties(
                    cursor, db, partition_table, partition_description
                )

                self.import_files(
                    cursor, db, pedigree_table, [pedigree_hdfs_path])

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
