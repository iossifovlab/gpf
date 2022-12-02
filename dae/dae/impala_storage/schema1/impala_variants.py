import logging
import queue
import time

from contextlib import closing
from typing import Dict, Any, Tuple, Set

import pyarrow as pa  # type: ignore
from impala.util import as_pandas  # type: ignore
from sqlalchemy.exc import TimeoutError as SqlTimeoutError

from dae.person_sets import PersonSetCollection

from dae.inmemory_storage.raw_variants import RawFamilyVariants

from dae.annotation.schema import Schema
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.parquet.schema1.serializers import AlleleParquetSerializer

from dae.variants.attributes import Role, Status, Sex

from dae.query_variants.query_runners import QueryResult, QueryRunner
from dae.query_variants.sql.schema1.schema1_query_director import \
    ImpalaQueryDirector
from dae.query_variants.sql.schema1.family_variants_query_builder import \
    FamilyVariantsQueryBuilder
from dae.query_variants.sql.schema1.summary_variants_query_builder import \
    SummaryVariantsQueryBuilder


logger = logging.getLogger(__name__)


class ImpalaQueryRunner(QueryRunner):
    """Run a query in a separate thread."""

    def __init__(self, connection_pool, query, deserializer=None):
        super().__init__(deserializer=deserializer)

        self.connection_pool = connection_pool
        self.query = query

    def connect(self):
        """Connect to the connection pool and return the connection."""
        started = time.time()
        while True:
            try:
                connection = self.connection_pool.connect()
                return connection
            except SqlTimeoutError:
                elapsed = time.time() - started
                logger.debug(
                    "runner (%s) timeout in connect; elapsed %0.2fsec",
                    self.study_id, elapsed)
                if self.closed():
                    logger.info(
                        "runner (%s) closed before connection established "
                        "after %0.2fsec",
                        self.study_id, elapsed)
                    return None

    def run(self):
        started = time.time()
        if self.closed():
            logger.info(
                "impala runner (%s) closed before executing...",
                self.study_id)
            return

        logger.debug(
            "impala runner (%s) started; "
            "connectio pool: %s",
            self.study_id, self.connection_pool.status())

        connection = self.connect()

        if connection is None:
            self._finalize(started)
            return

        with closing(connection) as connection:
            elapsed = time.time() - started
            logger.debug(
                "runner (%s) waited %0.2fsec for connection",
                self.study_id, elapsed)
            with connection.cursor() as cursor:
                try:
                    if self.closed():
                        logger.info(
                            "runner (%s) closed before execution "
                            "after %0.2fsec",
                            self.study_id, elapsed)
                        self._finalize(started)
                        return

                    cursor.execute_async(self.query)
                    self._wait_cursor_executing(cursor)

                    while not self.closed():
                        row = cursor.fetchone()
                        if row is None:
                            break
                        val = self.deserializer(row)

                        if val is None:
                            continue

                        self._put_value_in_result_queue(val)

                        if self.closed():
                            logger.debug(
                                "query runner (%s) closed while iterating",
                                self.study_id)
                            break

                except Exception as ex:  # pylint: disable=broad-except
                    logger.debug(
                        "exception in runner (%s) run: %s",
                        self.study_id, type(ex), exc_info=True)
                finally:
                    logger.debug(
                        "runner (%s) closing connection", self.study_id)

        self._finalize(started)

    def _put_value_in_result_queue(self, val):
        no_interest = 0
        while True:
            try:
                self._result_queue.put(val, timeout=0.1)
                break
            except queue.Full:
                logger.debug(
                    "runner (%s) nobody interested",
                    self.study_id)

                if self.closed():
                    break
                no_interest += 1
                if no_interest % 1_000 == 0:
                    logger.warning(
                        "runner (%s) nobody interested %s",
                        self.study_id, no_interest)
                if no_interest > 5_000:
                    logger.warning(
                        "runner (%s) nobody interested %s"
                        "closing...",
                        self.study_id, no_interest)
                    self.close()
                    break

    def _wait_cursor_executing(self, cursor):
        while True:
            if self.closed():
                logger.debug(
                    "query runner (%s) closed while executing",
                    self.study_id)
                break
            if not cursor.is_executing():
                logger.debug(
                    "query runner (%s) execution finished",
                    self.study_id)
                break
            time.sleep(0.1)

    def _finalize(self, started):
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.study_id, elapsed)
        logger.debug("connection pool: %s", self.connection_pool.status())


class ImpalaVariants:
    # pylint: disable=too-many-instance-attributes
    """A backend implementing an impala backend."""

    def __init__(
            self,
            impala_helpers,
            db,
            variants_table,
            pedigree_table,
            gene_models=None):
        super().__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        self.db = db
        self.variants_table = variants_table
        self.pedigree_table = pedigree_table

        self._impala_helpers = impala_helpers
        self.pedigree_schema = self._fetch_pedigree_schema()

        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)
        # Temporary workaround for studies that are imported without tags
        # e.g. production data that is too large to reimport
        FamiliesLoader._build_families_tags(
            self.families, {"ped_tags": True}
        )

        self.schema = self._fetch_variant_schema()
        if self.variants_table:
            study_id = variants_table.replace("_variants", "").lower()
            self.summary_variants_table = f"{study_id}_summary_variants"
            self.has_summary_variants_table = \
                self._check_summary_variants_table()
            self.serializer = AlleleParquetSerializer(self.schema)

        assert gene_models is not None
        self.gene_models = gene_models

        self.table_properties = dict({
            "region_length": 0,
            "chromosomes": [],
            "family_bin_size": 0,
            "coding_effect_types": [],
            "rare_boundary": 0
        })
        self._fetch_tblproperties()

    def connection(self):
        conn = self._impala_helpers.connection()
        logger.debug(
            "ImpalaVariants: getting connection to host %s "
            "from impala helpers %s", conn.host, id(self._impala_helpers))
        return conn

    @property
    def connection_pool(self):
        # pylint: disable=protected-access
        return self._impala_helpers._connection_pool

    @property
    def executor(self):
        assert self._impala_helpers.executor is not None
        return self._impala_helpers.executor

    def build_summary_variants_query_runner(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None):
        """Build a query selecting the appropriate summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            return None

        sv_table = None
        if self.has_summary_variants_table:
            sv_table = self.summary_variants_table
        query_builder = SummaryVariantsQueryBuilder(
            self.db, self.variants_table, self.pedigree_table,
            self.schema, self.table_properties,
            self.pedigree_schema, self.ped_df,
            self.gene_models, summary_variants_table=sv_table
        )
        if limit is None:
            request_limit = None
        elif limit < 0:
            request_limit = None
        else:
            request_limit = limit

        director = ImpalaQueryDirector(query_builder)
        director.build_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=request_limit,
        )

        deserialize_row = query_builder.create_row_deserializer(
            self.serializer
        )

        query = query_builder.product
        logger.debug("SUMMARY VARIANTS QUERY: %s", query)

        runner = ImpalaQueryRunner(
            self.connection_pool, query, deserializer=deserialize_row)

        filter_func = RawFamilyVariants.summary_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit)

        runner.adapt(filter_func)

        return runner

    @staticmethod
    def build_person_set_collection_query(
            person_set_collection: PersonSetCollection,
            person_set_collection_query: Tuple[str, Set[str]]):
        """No idea what it does. If you know please edit."""
        collection_id, selected_person_sets = person_set_collection_query
        assert collection_id == person_set_collection.id
        selected_person_sets = set(selected_person_sets)
        assert isinstance(selected_person_sets, set)

        if not person_set_collection.is_pedigree_only():
            return None

        available_person_sets = set(person_set_collection.person_sets.keys())
        if (available_person_sets & selected_person_sets) == \
                available_person_sets:
            return ()

        def pedigree_columns(selected_person_sets):
            result = []
            for person_set_id in sorted(selected_person_sets):
                if person_set_id not in person_set_collection.person_sets:
                    continue
                person_set = person_set_collection.person_sets[person_set_id]
                assert len(person_set.values) == \
                    len(person_set_collection.sources)
                person_set_query = {}
                for source, value in zip(
                        person_set_collection.sources, person_set.values):
                    person_set_query[source.ssource] = value
                result.append(person_set_query)
            return result

        if person_set_collection.default.id not in selected_person_sets:
            return (pedigree_columns(selected_person_sets), [])
        return (
            [],
            pedigree_columns(available_person_sets - selected_person_sets)
        )

    def build_family_variants_query_runner(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            pedigree_fields=None):
        """Build a query selecting the appropriate family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            logger.debug(
                "missing varants table... skipping")
            return None
        do_join = False
        if pedigree_fields is not None:
            do_join = True
        query_builder = FamilyVariantsQueryBuilder(
            self.db, self.variants_table, self.pedigree_table,
            self.schema, self.table_properties,
            self.pedigree_schema, self.ped_df,
            self.families, gene_models=self.gene_models,
            do_join=do_join,
        )
        director = ImpalaQueryDirector(query_builder)
        if limit is None:
            request_limit = None
        elif limit < 0:
            request_limit = None
        else:
            request_limit = limit

        director.build_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=request_limit,
            pedigree_fields=pedigree_fields
        )

        query = query_builder.product

        logger.debug("FAMILY VARIANTS QUERY: %s", query)
        deserialize_row = query_builder.create_row_deserializer(
            self.serializer)
        assert deserialize_row is not None

        runner = ImpalaQueryRunner(
            self.connection_pool, query, deserializer=deserialize_row)

        filter_func = RawFamilyVariants.family_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit)

        runner.adapt(filter_func)

        return runner

    def query_summary_variants(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None):
        """Query summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            return

        if limit is None:
            limit = -1
            request_limit = -1
        else:
            request_limit = 10 * limit

        runner = self.build_summary_variants_query_runner(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=request_limit
        )

        result = QueryResult(runners=[runner], limit=limit)
        logger.debug("starting result")
        result.start()

        seen = set()

        with closing(result) as result:

            for v in result:
                if v is None:
                    continue
                if v.svuid in seen:
                    continue
                if v is None:
                    continue
                yield v
                seen.add(v.svuid)

    def query_variants(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            pedigree_fields=None):
        """Query family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            return

        if limit is None:
            limit = -1
            request_limit = -1
        else:
            request_limit = 10 * limit

        runner = self.build_family_variants_query_runner(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=request_limit,
            pedigree_fields=pedigree_fields)

        result = QueryResult(runners=[runner], limit=limit)
        logger.debug("starting result")

        result.start()

        with closing(result) as result:
            seen = set()
            for v in result:
                if v is None:
                    continue
                if v.fvuid in seen:
                    continue
                yield v
                seen.add(v.fvuid)

    def _fetch_pedigree(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"SELECT * FROM {self.db}.{self.pedigree_table}"""

                cursor.execute(query)
                ped_df = as_pandas(cursor)

        columns = {
            "personId": "person_id",
            "familyId": "family_id",
            "momId": "mom_id",
            "dadId": "dad_id",
            "sampleId": "sample_id",
            "sex": "sex",
            "status": "status",
            "role": "role",
            "generated": "generated",
            "layout": "layout",
            "phenotype": "phenotype",
        }
        if "not_sequenced" in self.pedigree_schema:
            columns = {
                "not_sequenced": "not_sequenced"
            }

        ped_df = ped_df.rename(columns=columns)

        ped_df.role = ped_df.role.apply(Role)
        ped_df.sex = ped_df.sex.apply(Sex)
        ped_df.status = ped_df.status.apply(Status)

        return ped_df

    TYPE_MAP: Dict[str, Any] = {
        "str": (str, pa.string()),
        "float": (float, pa.float32()),
        "float32": (float, pa.float32()),
        "float64": (float, pa.float64()),
        "int": (int, pa.int32()),
        "int8": (int, pa.int8()),
        "tinyint": (int, pa.int8()),
        "int16": (int, pa.int16()),
        "smallint": (int, pa.int16()),
        "int32": (int, pa.int32()),
        "int64": (int, pa.int64()),
        "bigint": (int, pa.int64()),
        "list(str)": (list, pa.list_(pa.string())),
        "list(float)": (list, pa.list_(pa.float64())),
        "list(int)": (list, pa.list_(pa.int32())),
        "bool": (bool, pa.bool_()),
        "boolean": (bool, pa.bool_()),
        "binary": (bytes, pa.binary()),
        "string": (bytes, pa.string()),
    }

    def _fetch_variant_schema(self):
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"DESCRIBE {self.db}.{self.variants_table}"
                cursor.execute(query)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema_desc = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            schema = Schema()
            for name, type_name in schema_desc.items():
                py_type, _ = self.TYPE_MAP[type_name]
                schema.create_field(name, py_type)

            return schema

    def _fetch_pedigree_schema(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"DESCRIBE {self.db}.{self.pedigree_table}"
                cursor.execute(query)
                df = as_pandas(cursor)
                records = df[["name", "type"]].to_records()
                schema = {
                    col_name: col_type for (_, col_name, col_type) in records
                }
                return schema

    def _fetch_tblproperties(self):
        if not self.variants_table:
            return
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"DESCRIBE EXTENDED {self.db}.{self.variants_table}")
                rows = list(cursor)
                properties_start, properties_end = -1, -1
                for row_index, row in enumerate(rows):
                    if row[0].strip() == "Table Parameters:":
                        properties_start = row_index + 1

                    if (
                        properties_start != -1
                        and row[0] == ""
                        and row[1] is None
                        and row[2] is None
                    ):
                        properties_end = row_index + 1

                if properties_start == -1:
                    logger.debug("No partitioning found")
                    return

                for index in range(properties_start, properties_end):
                    prop_name = rows[index][1]
                    prop_value = rows[index][2]
                    if prop_name == \
                            "gpf_partitioning_region_bin_region_length":
                        self.table_properties["region_length"] = \
                            int(prop_value)
                    elif prop_name == \
                            "gpf_partitioning_region_bin_chromosomes":
                        chromosomes = prop_value.split(",")
                        chromosomes = \
                            list(map(str.strip, chromosomes))
                        self.table_properties["chromosomes"] = chromosomes
                    elif prop_name == \
                            "gpf_partitioning_family_bin_family_bin_size":
                        self.table_properties["family_bin_size"] = \
                            int(prop_value)
                    elif prop_name == \
                            "gpf_partitioning_coding_bin_coding_effect_types":
                        coding_effect_types = prop_value.split(",")
                        coding_effect_types = list(
                            map(str.strip, coding_effect_types))
                        self.table_properties["coding_effect_types"] = \
                            coding_effect_types
                    elif prop_name == \
                            "gpf_partitioning_frequency_bin_rare_boundary":
                        self.table_properties["rare_boundary"] = \
                            int(prop_value)

    def _check_summary_variants_table(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"SHOW TABLES IN {self.db} " \
                        f"LIKE '{self.summary_variants_table}'"
                cursor.execute(query)
                return len(cursor.fetchall()) == 1
