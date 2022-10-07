import os
import re
import time
import itertools
import logging

from contextlib import closing

from impala import dbapi  # type: ignore
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import TimeoutError as SqlTimeoutError


logger = logging.getLogger(__name__)


class ImpalaHelpers:
    """Helper methods for working with impala."""

    def __init__(self, impala_hosts, impala_port=21050, pool_size=1):

        if os.environ.get("DAE_IMPALA_HOST", None) is not None:
            impala_host = os.environ.get("DAE_IMPALA_HOST", None)
            logger.info("impala host overwritten: %s", impala_host)
            if impala_host is not None:
                impala_hosts = [impala_host]
        if impala_hosts is None:
            impala_hosts = []

        host_generator = itertools.cycle(impala_hosts)

        def create_connection():
            impala_host = next(host_generator)
            logger.debug("creating connection to impala host %s", impala_host)
            connection = dbapi.connect(host=impala_host, port=impala_port)
            connection.host = impala_host
            return connection

        if pool_size is None:
            pool_size = 3 * len(impala_host) + 1

        logger.info("impala connection pool size is: %s", pool_size)

        self._connection_pool = QueuePool(
            create_connection, pool_size=pool_size,
            reset_on_return=False,
            max_overflow=pool_size,
            timeout=1.0)

        logger.debug(
            "created impala pool with %s connections",
            self._connection_pool.status())

    def close(self):
        self._connection_pool.dispose()

    def connection(self, timeout: float = None):
        """Create a new connection to the impala host."""
        logger.debug("going to get impala connection from the pool; %s",
                     self._connection_pool.status())
        started = time.time()
        while True:
            try:
                connection = self._connection_pool.connect()
                return connection
            except SqlTimeoutError:
                elapsed = time.time() - started
                logger.debug(
                    "unable to connect; elapsed %0.2fsec", elapsed)
                if timeout is not None and elapsed > timeout:
                    return None

    @staticmethod
    def _import_single_file(cursor, db, table, import_file):
        cursor.execute(
            f"""
            DROP TABLE IF EXISTS {db}.{table}
            """)

        dirname = os.path.dirname(import_file)
        statement = f"""
            CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{import_file}'
            STORED AS PARQUET LOCATION '{dirname}'
        """
        logger.debug("%s", statement)
        cursor.execute(statement)
        cursor.execute(f"REFRESH {db}.{table}")

    @staticmethod
    def _add_partition_properties(cursor, db, table, partition_description):
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
        coding_effect_types = coding_effect_types.replace("'", "\\'")
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

    @staticmethod
    def _create_dataset_table(
        cursor, db, table, sample_file, partition_description
    ):
        cursor.execute(
            f"DROP TABLE IF EXISTS {db}.{table}")

        hdfs_dir = partition_description.variants_filename_basedir(sample_file)
        if not partition_description.has_partitions():
            statement = f"""
                CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{sample_file}'
                STORED AS PARQUET LOCATION '{hdfs_dir}'
            """
        else:
            partitions = partition_description.build_impala_partitions()
            statement = f"""
                CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{sample_file}'
                PARTITIONED BY ({partitions})
                STORED AS PARQUET LOCATION '{hdfs_dir}'
            """
        cursor.execute(statement)

        if partition_description.has_partitions():
            cursor.execute(
                f"ALTER TABLE {db}.{table} RECOVER PARTITIONS")
        cursor.execute(
            f"REFRESH {db}.{table}")

    def import_pedigree_into_db(self, db, pedigree_table, pedigree_hdfs_file):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {db}")

                self._import_single_file(
                    cursor, db, pedigree_table, pedigree_hdfs_file)

    @staticmethod
    def _build_variants_schema(variants_schema):
        type_convertion = {
            "int32": "INT",
            "int16": "SMALLINT",
            "int8": "TINYINT",
            "float": "FLOAT",
            "string": "STRING",
            "binary": "STRING",
        }
        result = []
        for field_name, field_type in variants_schema.items():
            impala_type = type_convertion.get(field_type)
            assert impala_type is not None, (field_name, field_type)
            result.append(f"`{field_name}` {impala_type}")
        statement = ", ".join(result)
        statement = f"( {statement} )"
        return statement

    def _build_import_variants_statement(
            self, db, variants_table, variants_hdfs_dir,
            partition_description,
            variants_sample=None,
            variants_schema=None):

        assert variants_sample is not None or variants_schema is not None

        statement = [
            "CREATE EXTERNAL TABLE", f"{db}.{variants_table}"]
        if variants_schema is not None:
            statement.append(
                self._build_variants_schema(variants_schema))
        else:
            assert variants_sample is not None
            statement.extend(
                ["LIKE PARQUET", f"'{variants_sample}'"])

        if partition_description.has_partitions():
            partitions = partition_description.build_impala_partitions()
            statement.extend([
                "PARTITIONED BY", f"({partitions})"
            ])

        statement.extend([
            "STORED AS PARQUET LOCATION",
            f"'{variants_hdfs_dir}'"
        ])
        return " ".join(statement)

    def import_variants_into_db(
            self, db, variants_table, variants_hdfs_dir,
            partition_description,
            variants_sample=None,
            variants_schema=None):
        """Import variant parquet files in variants_hdfs_dir in impala."""
        assert variants_schema is not None or variants_sample is not None

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {db}")

                cursor.execute(
                    f"DROP TABLE IF EXISTS {db}.{variants_table}")

                statement = self._build_import_variants_statement(
                    db, variants_table, variants_hdfs_dir,
                    partition_description,
                    variants_sample=variants_sample,
                    variants_schema=variants_schema)
                logger.info("going to execute: %s", statement)
                cursor.execute(statement)

                if partition_description.has_partitions():
                    cursor.execute(
                        f"ALTER TABLE {db}.{variants_table} "
                        f"RECOVER PARTITIONS")
                cursor.execute(
                    f"REFRESH {db}.{variants_table}")

                if partition_description.has_partitions():
                    self._add_partition_properties(
                        cursor, db, variants_table, partition_description)

    def get_table_create_statement(self, db, table):
        """Get the create statement for table."""
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                statement = f"SHOW CREATE TABLE {db}.{table}"
                cursor.execute(statement)

                create_statement = None
                for row in cursor:
                    create_statement = row[0]
                    break
                return create_statement

    def recreate_table(self, db, table, new_table, new_hdfs_dir):
        """Recreate a table."""
        create_statement = self.get_table_create_statement(db, table)
        assert create_statement is not None

        with closing(self.connection()) as conn:

            table_name = re.compile(
                r"CREATE EXTERNAL TABLE (?P<table_name>[a-zA-Z0-9._]+)\s")
            create_statement = table_name.sub(
                f"CREATE EXTERNAL TABLE {db}.{new_table} ",
                create_statement
            )

            location = re.compile(
                r"LOCATION '(?P<location>.+)'\s")
            create_statement = location.sub(
                f"LOCATION '{new_hdfs_dir}' ",
                create_statement
            )

            position = re.compile(
                r"\s(position)\s")

            create_statement = position.sub(
                " `position` ",
                create_statement
            )

            role = re.compile(
                r"\s(role)\s")

            create_statement = role.sub(
                " `role` ",
                create_statement
            )

            create_statement = create_statement.replace("3'UTR", "3\\'UTR")
            create_statement = create_statement.replace("5'UTR", "5\\'UTR")

            with conn.cursor() as cursor:
                cursor.execute(
                    f"DROP TABLE IF EXISTS {db}.{new_table}"
                )

                logger.info("going to execute %s", create_statement)
                cursor.execute(create_statement)

                if "PARTITIONED" in create_statement:
                    cursor.execute(
                        f"ALTER TABLE {db}.{new_table} "
                        f"RECOVER PARTITIONS")
                cursor.execute(
                    f"REFRESH {db}.{new_table}")

    def rename_table(self, db, table, new_table):
        """Rename db.table to new_table."""
        statement = [
            f"ALTER TABLE {db}.{table} RENAME TO {db}.{new_table}"
        ]
        statement = " ".join(statement)
        logger.info("going to execute %s", statement)

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(statement)

    def check_database(self, dbname):
        """Check if dbname exists."""
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = "SHOW DATABASES"
                cursor.execute(query)
                for row in cursor:
                    if row[0] == dbname:
                        return True
        return False

    def check_table(self, dbname, tablename):
        """Check if dbname.tablename exists."""
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"SHOW TABLES IN {dbname}"
                cursor.execute(query)
                for row in cursor:
                    if row[0] == tablename.lower():
                        return True
        return False

    def drop_table(self, dbname, tablename):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"DROP TABLE IF EXISTS {dbname}.{tablename}"
                cursor.execute(query)

    def create_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"CREATE DATABASE IF NOT EXISTS {dbname}"
                cursor.execute(query)

    def drop_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"DROP DATABASE IF EXISTS {dbname} CASCADE")
