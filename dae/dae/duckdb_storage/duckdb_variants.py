import time
import json
import logging
import queue
from typing import Optional, Any, cast, Generator, ContextManager
import contextlib
import threading

import duckdb
import numpy as np
import pandas as pd

from dae.genomic_resources.gene_models import GeneModels
from dae.variants.attributes import Role, Status, Sex, Inheritance
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.variants.variant import SummaryVariantFactory, SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.query_variants.query_runners import QueryRunner

logger = logging.getLogger(__name__)


_DUCKDB_LOCK = threading.Lock()


@contextlib.contextmanager
def duckdb_global_connect(
) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    with _DUCKDB_LOCK:
        yield cast(duckdb.DuckDBPyConnection, duckdb)


@contextlib.contextmanager
def duckdb_db_connect(
    db_name: str, read_only: bool = True
) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    logger.info("duckdb internal connection to %s", db_name)
    yield duckdb.connect(db_name, read_only=read_only)


class DuckDbRunner(QueryRunner):
    """Run a DuckDb query in a separate thread."""

    def __init__(
            self,
            connection_factory: ContextManager[duckdb.DuckDBPyConnection],
            query: str,
            deserializer: Optional[Any] = None):
        super().__init__(deserializer=deserializer)

        self.connection = connection_factory
        self.query = query

    def run(self) -> None:
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        logger.debug(
            "bigquery runner (%s) started", self.study_id)

        try:
            if self.is_closed():
                logger.info(
                    "runner (%s) closed before execution",
                    self.study_id)
                self._finalize(started)
                return

            with self.connection as connection:
                for record in connection.execute(self.query).fetchall():
                    val = self.deserializer(record)
                    if val is None:
                        continue
                    self._put_value_in_result_queue(val)
                    if self.is_closed():
                        logger.debug(
                            "query runner (%s) closed while iterating",
                            self.query)
                        break

        except Exception as ex:  # pylint: disable=broad-except
            logger.error(
                "exception in runner (%s) run: %s",
                self.query, type(ex), exc_info=True)
            self._put_value_in_result_queue(ex)
        finally:
            logger.debug(
                "runner (%s) closing connection", self.query)

        self._finalize(started)

    def _put_value_in_result_queue(self, val: Any) -> None:
        assert self._result_queue is not None

        no_interest = 0
        while True:
            try:
                self._result_queue.put(val, timeout=0.1)
                break
            except queue.Full:
                logger.debug(
                    "runner (%s) nobody interested",
                    self.query)

                if self.is_closed():
                    break
                no_interest += 1
                if no_interest % 1_000 == 0:
                    logger.warning(
                        "runner (%s) nobody interested %s",
                        self.query, no_interest)
                if no_interest > 5_000:
                    logger.warning(
                        "runner (%s) nobody interested %s"
                        "closing...",
                        self.query, no_interest)
                    self.close()
                    break

    def _finalize(self, started: float) -> None:
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.query, elapsed)


class DuckDbQueryDialect(Dialect):
    """Abstracts away details related to bigquery."""

    def __init__(self, ns: Optional[str] = None):
        super().__init__(namespace=ns)

    @staticmethod
    def add_unnest_in_join() -> bool:
        return True

    @staticmethod
    def int_type() -> str:
        return "int"

    @staticmethod
    def float_type() -> str:
        return "float"

    @staticmethod
    def array_item_suffix() -> str:
        return ""

    @staticmethod
    def use_bit_and_function() -> bool:
        return False

    @staticmethod
    def escape_char() -> str:
        return ""

    @staticmethod
    def escape_quote_char() -> str:
        return "'"

    def build_table_name(self, table: str, db: str) -> str:
        return table

    def build_array_join(self, column: str, allias: str) -> str:
        return f"\n    CROSS JOIN\n        " \
            f"(SELECT UNNEST({column}) AS {allias})"


class DuckDbVariants(SqlSchema2Variants):
    """Backend for BigQuery."""

    RUNNER_CLASS = DuckDbRunner

    def __init__(
        self,
        db: Optional[str],
        family_variant_table: Optional[str],
        summary_allele_table: Optional[str],
        pedigree_table: str,
        meta_table: str,
        gene_models: Optional[GeneModels] = None,
    ) -> None:
        super().__init__(
            DuckDbQueryDialect(),
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models)
        assert pedigree_table, pedigree_table
        self.start_time = time.time()

    def _fetch_tblproperties(self) -> str:
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'partition_description'
               LIMIT 1
            """

        with self._get_connection_factory() as connection:
            result = connection.execute(query).fetchall()
            for row in result:
                return cast(str, row[0])
            return ""

    def _fetch_summary_schema(self) -> dict[str, str]:
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'summary_schema'
               LIMIT 1
            """

        schema_content = ""
        with self._get_connection_factory() as connection:
            result = connection.execute(query).fetchall()
            for row in result:
                schema_content = row[0]
        return dict(line.split("|") for line in schema_content.split("\n"))

    def _fetch_family_schema(self) -> dict[str, str]:
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'family_schema'
               LIMIT 1
            """

        schema_content = ""
        with self._get_connection_factory() as connection:
            rows = connection.execute(query).fetchall()
            for row in rows:
                schema_content = row[0]
        return dict(line.split("|") for line in schema_content.split("\n"))

    def _fetch_schema(self, table: str) -> dict[str, str]:
        return {}

    def _fetch_pedigree(self) -> pd.DataFrame:
        query = f"SELECT * FROM {self.pedigree_table}"
        with self._get_connection_factory() as connection:
            ped_df = cast(pd.DataFrame, connection.execute(query).df())
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

            ped_df = ped_df.rename(columns=columns)
            ped_df.role = ped_df.role.apply(Role.from_value)
            ped_df.sex = ped_df.sex.apply(Sex.from_value)
            ped_df.status = ped_df.status.apply(Status.from_value)
            ped_df.loc[ped_df.layout.isna(), "layout"] = None

            return ped_df

    def _get_connection_factory(self) -> Any:
        if self.db is not None:
            return duckdb_db_connect(self.db)
        return duckdb_global_connect()

    def _deserialize_summary_variant(self, record: str) -> SummaryVariant:
        sv_record = json.loads(record[2])
        return SummaryVariantFactory.summary_variant_from_records(
            sv_record
        )

    def _deserialize_family_variant(self, record: list[str]) -> FamilyVariant:
        sv_record = json.loads(record[4])
        fv_record = json.loads(record[5])
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members
        )
