import time
import json
import logging
import queue
from typing import Optional, Any

import duckdb
import numpy as np

from dae.variants.attributes import Role, Status, Sex
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.query_variants.query_runners import QueryRunner

logger = logging.getLogger(__name__)


class DuckDbRunner(QueryRunner):
    """Run a DuckDb query in a separate thread."""

    def __init__(self, connection_factory, query, deserializer=None):
        super().__init__(deserializer=deserializer)

        self.client = connection_factory
        self.query = query

    def run(self):
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        logger.debug(
            "bigquery runner (%s) started", self.study_id)

        try:
            if self.closed():
                logger.info(
                    "runner (%s) closed before execution",
                    self.study_id)
                self._finalize(started)
                return

            for record in self.client.execute(self.query).fetchall():
                val = self.deserializer(record)
                if val is None:
                    continue
                self._put_value_in_result_queue(val)
                if self.closed():
                    logger.debug(
                        "query runner (%s) closed while iterating",
                        self.study_id)
                    break

        except Exception as ex:  # pylint: disable=broad-except
            logger.error(
                "exception in runner (%s) run: %s",
                self.study_id, type(ex), exc_info=True)
            self._put_value_in_result_queue(ex)
        finally:
            logger.debug(
                "runner (%s) closing connection", self.study_id)

        self._finalize(started)

    def _put_value_in_result_queue(self, val):
        assert self._result_queue is not None

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

    def _finalize(self, started):
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.study_id, elapsed)


class DuckDbQueryDialect(Dialect):
    """Abstracts away details related to bigquery."""

    def __init__(self, ns: Optional[str] = None):
        super().__init__(namespace=ns)

    @staticmethod
    def add_unnest_in_join() -> bool:
        return True

    @staticmethod
    def int_type() -> str:
        return "INT64"

    @staticmethod
    def float_type() -> str:
        return "FLOAT64"

    @staticmethod
    def array_item_suffix() -> str:
        return ""

    @staticmethod
    def use_bit_and_function() -> bool:
        return False

    def build_table_name(self, table: str, db: str) -> str:
        return table


class DuckDbVariants(SqlSchema2Variants):
    """Backend for BigQuery."""

    RUNNER_CLASS = DuckDbRunner

    def __init__(
        self,
        db,
        family_variant_table,
        summary_allele_table,
        pedigree_table,
        meta_table,
        gene_models=None,
    ):
        self.connection = duckdb.connect(db)

        super().__init__(
            DuckDbQueryDialect(),
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models)
        assert db, db
        assert pedigree_table, pedigree_table
        self.start_time = time.time()

    def _fetch_tblproperties(self):
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'partition_description'
               LIMIT 1
            """

        result = self.connection.execute(query).fetchall()
        for row in result:
            return row[0]
        return ""

    def _fetch_schema(self, table) -> dict[str, str]:
        query = f"""DESCRIBE {table}"""
        df = self.connection.execute(query).df()
        records = df[["column_name", "column_type"]].to_records()
        schema = {
            col_name: col_type for (_, col_name, col_type) in records
        }
        return schema

    def _fetch_pedigree(self):
        query = f"SELECT * FROM {self.pedigree_table}"

        # ped_df = pandas_gbq.read_gbq(q, project_id=self.gcp_project_id)
        ped_df = self.connection.execute(query).df()
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
        ped_df.role = ped_df.role.apply(Role)  # type: ignore
        ped_df.sex = ped_df.sex.apply(Sex)  # type: ignore
        ped_df.status = ped_df.status.apply(Status)  # type: ignore

        return ped_df

    def _get_connection_factory(self) -> Any:
        # pylint: disable=protected-access
        return self.connection

    def _deserialize_summary_variant(self, record):
        sv_record = json.loads(record[2])
        return SummaryVariantFactory.summary_variant_from_records(
            sv_record
        )

    def _deserialize_family_variant(self, record):
        sv_record = json.loads(record[4])
        fv_record = json.loads(record[5])

        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
        )
