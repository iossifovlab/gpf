import os
import re
import itertools
import logging
import traceback

# from dae.utils.debug_closing import closing
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue, Full

from impala import dbapi
from sqlalchemy.pool import QueuePool


logger = logging.getLogger(__name__)


class ImpalaQueryRunner:

    def __init__(
            self, connection, query, result_queue, deserializer=None):
        super(ImpalaQueryRunner, self).__init__()
        self.connection = connection
        self.cursor = connection.cursor()
        self.query = query
        self.result_queue = result_queue
        self._future = None
        self._owner = None
        if deserializer is not None:
            self.deserializer = deserializer
        else:
            self.deserializer = lambda v: v

    def start(self):
        assert self._owner is not None
        self._future = self._owner.executor.submit(self.run)

    def started(self):
        return self._future is not None

    def closed(self):
        return self.cursor._closed

    def run(self):
        try:
            self.cursor.execute(self.query)
            while not self.closed():
                row = self.cursor.fetchone()
                val = self.deserializer(row)

                if self.result_queue.full():
                    logger.debug(
                        f"queue is full ({self.result_queue.qsize()}); "
                        f"going to block")
                while True:
                    try:
                        self.result_queue.put(val, timeout=0.1)
                    except Full:
                        if self.closed():
                            break

        except BaseException as ex:
            logger.debug(
                f"exception in runner run: {type(ex)}", exc_info=True)
        finally:
            self.connection.close()
        logger.debug("runner done")

    def close(self):
        try:
            self.cursor.close()
        except BaseException as ex:
            logger.debug(
                f"exception in runner close: {type(ex)}", exc_info=True)
        self._owner = None
        logger.debug("runner closed")

    def _set_future(self, future):
        self._future = future

    def done(self):
        return self._future.done()


class ImpalaQueryResult:
    def __init__(self, result_queue, runners):
        self.result_queue = result_queue
        self.runners = runners

    def done(self):
        return all([r.done() for r in self.runners])

    def __iter__(self):
        return self

    def __next__(self):
        if self.done():
            print("don't even try; runner done")
            raise StopIteration()

        try:
            row = self.result_queue.get(timeout=0.1)
            return row
        except Empty:
            if self.done():
                print("result done")
                raise StopIteration()

    def get(self, timeout=0):
        try:
            row = self.result_queue.get(timeout=timeout)
            return row
        except Empty:
            if self.done():
                raise StopIteration()

    def start(self):
        for runner in self.runners:
            runner.start()

    def close(self):
        for runner in self.runners:
            try:
                runner.close()
            except BaseException as ex:
                print("exception in result close:", type(ex))
                traceback.print_tb(ex.__traceback__)
        while not self.result_queue.empty():
            self.result_queue.get()


class ImpalaHelpers(object):

    def __init__(self, impala_hosts, impala_port=21050, pool_size=20):

        if os.environ.get("DAE_IMPALA_HOST", None) is not None:
            impala_host = os.environ.get("DAE_IMPALA_HOST", None)
            logger.info(f"impala host overwritten: {impala_host}")
            if impala_host is not None:
                impala_hosts = [impala_host]
        if impala_hosts is None:
            impala_hosts = []

        self.executor = ThreadPoolExecutor(max_workers=len(impala_hosts))

        host_generator = itertools.cycle(impala_hosts)

        def create_connection():
            impala_host = next(host_generator)
            logger.debug(f"creating connection to impala host {impala_host}")
            connection = dbapi.connect(host=impala_host, port=impala_port)
            connection.host = impala_host
            return connection

        self._connection_pool = QueuePool(
            create_connection, pool_size=20,  # pool_size,
            reset_on_return=False,
            # use_threadlocal=True,
        )
        logger.debug(
            f"created impala pool with {self._connection_pool.status()} "
            f"connections")
        # connections = []
        # for i in range(20):
        #     conn = self.connection()
        #     conn.id = i
        #     connections.append(conn)
        # for conn in connections:
        #     conn.close()

    def connection(self):
        logger.debug(
            f"going to get impala connection from the pool; "
            f"{self._connection_pool.status()}")
        conn = self._connection_pool.connect()
        logger.debug(
            f"[DONE] going to get impala connection to host {conn.host} "
            f"from the pool; {self._connection_pool.status()}")
        return conn

    def _submit(self, query, result_queue):
        connection = self.connection()
        runner = ImpalaQueryRunner(connection, query, result_queue)
        runner._owner = self
        return runner

    def _map(self, queries, result_queue):
        runners = []
        for query in queries:
            runner = self._submit(query, result_queue)
            runners.append(runner)
        return runners

    def submit(self, query):
        result_queue = Queue(maxsize=1_000)
        runner = self._submit(query, result_queue)
        result = ImpalaQueryResult(result_queue, [runner])
        return result

    def map(self, queries):
        result_queue = Queue(maxsize=1_000)
        runners = []
        for query in queries:
            runner = self._submit(query, result_queue)
            runners.append(runner)

        result = ImpalaQueryResult(result_queue, runners)
        return result

    def _import_single_file(self, cursor, db, table, import_file):

        cursor.execute(
            f"""
            DROP TABLE IF EXISTS {db}.{table}
            """)

        dirname = os.path.dirname(import_file)
        statement = f"""
            CREATE EXTERNAL TABLE {db}.{table} LIKE PARQUET '{import_file}'
            STORED AS PARQUET LOCATION '{dirname}'
        """
        logger.debug(f"{statement}")
        cursor.execute(statement)
        cursor.execute(f"REFRESH {db}.{table}")

    def _add_partition_properties(
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

    def _create_dataset_table(
            self, cursor, db, table,
            sample_file,
            pd):

        cursor.execute(
            f"DROP TABLE IF EXISTS {db}.{table}")

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

    def _build_variants_schema(self, variants_schema):
        TYPE_CONVERTION = {
            "int32": "INT",
            "int16": "SMALLINT",
            "int8": "TINYINT",
            "float": "FLOAT",
            "string": "STRING",
            "binary": "STRING",

        }
        result = []
        for field_name, field_type in variants_schema.items():
            impala_type = TYPE_CONVERTION.get(field_type)
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
                # statement = " ".join(statement)
                logger.info(f"going to execute: {statement}")
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
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                statement = f"SHOW CREATE TABLE {db}.{table}"
                cursor.execute(statement)

                create_statement = None
                for row in cursor:
                    create_statement = row[0]
                    break
                return create_statement

    def recreate_table(
            self, db, table, new_table, new_hdfs_dir):

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

                logger.info(f"going to execute {create_statement}")
                cursor.execute(create_statement)

                if "PARTITIONED" in create_statement:
                    cursor.execute(
                        f"ALTER TABLE {db}.{new_table} "
                        f"RECOVER PARTITIONS")
                cursor.execute(
                    f"REFRESH {db}.{new_table}")

    def rename_table(
            self, db, table, new_table):
        statement = [
            f"ALTER TABLE {db}.{table} RENAME TO {db}.{new_table}"
        ]
        statement = " ".join(statement)
        logger.info(f"going to execute {statement}")

        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(statement)

    def check_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = "SHOW DATABASES"
                cursor.execute(q)
                for row in cursor:
                    if row[0] == dbname:
                        return True
        return False

    def check_table(self, dbname, tablename):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = f"SHOW TABLES IN {dbname}"
                cursor.execute(q)
                for row in cursor:
                    if row[0] == tablename.lower():
                        return True
        return False

    def drop_table(self, dbname, tablename):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = f"DROP TABLE IF EXISTS {dbname}.{tablename}"
                cursor.execute(q)

    def create_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = f"CREATE DATABASE IF NOT EXISTS {dbname}"
                cursor.execute(q)

    def drop_database(self, dbname):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"DROP DATABASE IF EXISTS {dbname} CASCADE")
