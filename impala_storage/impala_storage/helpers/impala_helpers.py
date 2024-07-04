import itertools
import logging
import os
import re
import time
from contextlib import closing
from typing import Any

from impala import dbapi
from impala.hiveserver2 import HiveServer2Connection
from sqlalchemy import exc, pool

from dae.parquet.partition_descriptor import PartitionDescriptor

logger = logging.getLogger(__name__)


class ImpalaHelpers:
    """Helper methods for working with impala."""

    def __init__(
        self, impala_hosts: list[str] | None,
        impala_port: int = 21050, pool_size: int | None = 1,
    ):

        if os.environ.get("DAE_IMPALA_HOST", None) is not None:
            impala_host = os.environ.get("DAE_IMPALA_HOST", None)
            logger.info("impala host overwritten: %s", impala_host)
            if impala_host is not None:
                impala_hosts = [impala_host]
        if impala_hosts is None:
            raise ValueError("impala hosts are not configured")

        host_generator = itertools.cycle(impala_hosts)

        def create_connection() -> HiveServer2Connection:
            impala_host = next(host_generator)
            logger.debug("creating connection to impala host %s", impala_host)
            connection = dbapi.connect(host=impala_host, port=impala_port)
            connection.host = impala_host
            return connection

        if pool_size is None:
            pool_size = 3 * len(impala_hosts) + 1

        logger.info("impala connection pool size is: %s", pool_size)

        self._connection_pool = pool.QueuePool(
            create_connection, pool_size=pool_size,
            reset_on_return=False,
            max_overflow=pool_size,
            timeout=3)

        logger.debug(
            "created impala pool with %s connections",
            self._connection_pool.status())

    def close(self) -> None:
        self._connection_pool.dispose()

    def connection(
        self, timeout: int | None = None,
    ) -> pool.PoolProxiedConnection:
        """Create a new connection to the impala host."""
        logger.debug("getting impala connection from the pool; %s",
                     self._connection_pool.status())
        started = time.time()
        while True:
            try:
                connection = self._connection_pool.connect()
                return connection
            except exc.TimeoutError as error:
                elapsed = time.time() - started
                logger.debug(
                    "unable to connect; elapsed %0.2fsec", elapsed)
                if timeout is not None and elapsed > timeout:
                    raise TimeoutError(
                        f"unable to connect to impala for {elapsed:0.2f}sec",
                    ) from error

    @staticmethod
    def _import_single_file(
        cursor: Any, db: str, table: str, import_file: str,
    ) -> None:
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
    def _add_partition_properties(
        cursor: Any, db: str, table:
        str, partition_description: PartitionDescriptor,
    ) -> None:
        chromosomes = ", ".join(partition_description.chromosomes)
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_region_bin_chromosomes' = "
            f"'{chromosomes}'"
            ")",
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_region_bin_region_length' = "
            f"'{partition_description.region_length}'"
            ")",
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_family_bin_family_bin_size' = "
            f"'{partition_description.family_bin_size}'"
            ")",
        )
        coding_effect_types = ",".join(
            partition_description.coding_effect_types,
        )
        coding_effect_types = coding_effect_types.replace("'", "\\'")
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_coding_bin_coding_effect_types' = "
            f"'{coding_effect_types}'"
            ")",
        )
        cursor.execute(
            f"ALTER TABLE {db}.{table} "
            "SET TBLPROPERTIES("
            f"'gpf_partitioning_frequency_bin_rare_boundary' = "
            f"'{partition_description.rare_boundary}'"
            ")",
        )

    @staticmethod
    def _build_impala_partitions(
        partition_descriptor: PartitionDescriptor,
    ) -> str:
        partitions = partition_descriptor.dataset_family_partition()
        type_convertion = {
            "int32": "INT",
            "int16": "SMALLINT",
            "int8": "TINYINT",
            "float": "FLOAT",
            "string": "STRING",
            "binary": "STRING",
        }
        impala_partitions = ", ".join([
            f"{bname} {type_convertion[btype]}"
            for (bname, btype) in partitions
        ])
        return impala_partitions

    # @staticmethod
    # def _create_dataset_table(
    #     cursor: Any, db: str, table: str, sample_file: str,
    #     partition_description: PartitionDescriptor
    # ) -> None:
    #     cursor.execute(
    #         f"DROP TABLE IF EXISTS {db}.{table}")

    #     hdfs_dir = partition_description.variants_filename_basedir(
    #           sample_file)
    #     if not partition_description.has_partitions():
    #         statement = f"""
    #             CREATE EXTERNAL TABLE {db}.{table}
    #             LIKE PARQUET '{sample_file}'
    #             STORED AS PARQUET LOCATION '{hdfs_dir}'
    #         """
    #     else:
    #         impala_partitions = \
    #             ImpalaHelpers._build_impala_partitions(partition_description)
    #         statement = f"""
    #             CREATE EXTERNAL TABLE {db}.{table}
    #             LIKE PARQUET '{sample_file}'
    #             PARTITIONED BY ({impala_partitions})
    #             STORED AS PARQUET LOCATION '{hdfs_dir}'
    #         """
    #     cursor.execute(statement)

    #     if partition_description.has_partitions():
    #         cursor.execute(
    #             f"ALTER TABLE {db}.{table} RECOVER PARTITIONS")
    #     cursor.execute(
    #         f"REFRESH {db}.{table}")

    def import_pedigree_into_db(
        self, db: str, pedigree_table: str, pedigree_hdfs_file: str,
    ) -> None:
        """Import pedigree files into impala table."""
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {db}")

                self._import_single_file(
                    cursor, db, pedigree_table, pedigree_hdfs_file)

    @staticmethod
    def _build_variants_schema(variants_schema: dict[str, Any]) -> str:
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
        self, db: str, variants_table: str, variants_hdfs_dir: str,
        partition_description: PartitionDescriptor,
        variants_sample: str | None = None,
        variants_schema: dict[str, Any] | None = None,
    ) -> str:

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
            impala_partitions = \
                ImpalaHelpers._build_impala_partitions(partition_description)
            statement.extend([
                "PARTITIONED BY", f"({impala_partitions})",
            ])

        statement.extend([
            "STORED AS PARQUET LOCATION",
            f"'{variants_hdfs_dir}'",
        ])
        return " ".join(statement)

    def import_variants_into_db(
        self, db: str, variants_table: str, variants_hdfs_dir: str,
        partition_description: PartitionDescriptor,
        variants_sample: str | None = None,
        variants_schema: dict[str, Any] | None = None,
    ) -> None:
        """Import variant parquet files in variants_hdfs_dir in impala."""
        assert variants_schema is not None or variants_sample is not None

        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
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

    def compute_table_stats(
        self, db: str, table: str, region_bin: str | None = None,
    ) -> None:
        """Compute impala table stats."""
        with closing(self.connection()) as connection:
            with closing(connection.cursor()) as cursor:
                if region_bin is not None:
                    query = f"COMPUTE INCREMENTAL STATS {db}.{table} " \
                        f"PARTITION (region_bin='{region_bin}')"
                else:
                    query = f"COMPUTE STATS {db}.{table}"
                logger.info("compute stats for impala table: %s", query)
                cursor.execute(query)

    def collect_region_bins(
        self, db: str, table: str,
    ) -> list[str]:
        """Collect region bins from table."""
        region_bins = []
        with closing(self.connection()) as connection:
            with closing(connection.cursor()) as cursor:
                query = f"SELECT DISTINCT(region_bin) FROM " \
                    f"{db}.{table}"
                logger.info("running %s", query)
                cursor.execute(query)
                for row in cursor:  # type: ignore
                    region_bins.append(row[0])
        region_bins.sort()
        logger.info("collected region bins: %s", region_bins)
        return region_bins

    def get_table_create_statement(
        self, db: str, table: str,
    ) -> str | None:
        """Get the create statement for table."""
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                statement = f"SHOW CREATE TABLE {db}.{table}"
                cursor.execute(statement)

                create_statement = None
                for row in cursor:  # type: ignore
                    create_statement = row[0]
                    break
                return create_statement

    def recreate_table(
        self, db: str, table: str, new_table: str, new_hdfs_dir: str,
    ) -> None:
        """Recreate a table."""
        create_statement = self.get_table_create_statement(db, table)
        assert create_statement is not None

        with closing(self.connection()) as conn:

            table_name = re.compile(
                r"CREATE EXTERNAL TABLE (?P<table_name>[a-zA-Z0-9._]+)\s")
            create_statement = table_name.sub(
                f"CREATE EXTERNAL TABLE {db}.{new_table} ",
                create_statement,
            )

            location = re.compile(
                r"LOCATION '(?P<location>.+)'\s")
            create_statement = location.sub(
                f"LOCATION '{new_hdfs_dir}' ",
                create_statement,
            )

            position = re.compile(
                r"\s(position)\s")

            create_statement = position.sub(
                " `position` ",
                create_statement,
            )

            role = re.compile(
                r"\s(role)\s")

            create_statement = role.sub(
                " `role` ",
                create_statement,
            )

            create_statement = create_statement.replace("3'UTR", "3\\'UTR")
            create_statement = create_statement.replace("5'UTR", "5\\'UTR")

            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    f"DROP TABLE IF EXISTS {db}.{new_table}",
                )

                logger.info("going to execute %s", create_statement)
                cursor.execute(create_statement)

                if "PARTITIONED" in create_statement:
                    cursor.execute(
                        f"ALTER TABLE {db}.{new_table} "
                        f"RECOVER PARTITIONS")
                cursor.execute(
                    f"REFRESH {db}.{new_table}")

    def rename_table(
        self, db: str, table: str, new_table: str,
    ) -> None:
        """Rename db.table to new_table."""
        parts = [
            f"ALTER TABLE {db}.{table} RENAME TO {db}.{new_table}",
        ]
        statement = " ".join(parts)
        logger.info("going to execute %s", statement)

        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(statement)

    def check_database(self, dbname: str) -> bool:
        """Check if dbname exists."""
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = "SHOW DATABASES"
                cursor.execute(query)
                for row in cursor:  # type: ignore
                    if row[0] == dbname:
                        return True
        return False

    def check_table(self, dbname: str, tablename: str) -> bool:
        """Check if dbname.tablename exists."""
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"SHOW TABLES IN {dbname}"
                cursor.execute(query)
                for row in cursor:  # type: ignore
                    if row[0] == tablename.lower():
                        return True
        return False

    def drop_table(self, dbname: str, tablename: str) -> None:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"DROP TABLE IF EXISTS {dbname}.{tablename}"
                cursor.execute(query)

    def create_database(self, dbname: str) -> None:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"CREATE DATABASE IF NOT EXISTS {dbname}"
                cursor.execute(query)

    def drop_database(self, dbname: str) -> None:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    f"DROP DATABASE IF EXISTS {dbname} CASCADE")
