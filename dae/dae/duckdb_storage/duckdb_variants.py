import logging
import time
from typing import Any, cast

import duckdb
import pandas as pd
import yaml

from dae.duckdb_storage.duckdb_connection_factory import DuckDbConnectionFactory
from dae.genomic_resources.gene_models import GeneModels
from dae.query_variants.query_runners import QueryRunner
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.variants.attributes import Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


class DuckDbRunner(QueryRunner):
    """Run a DuckDb query in a separate thread."""

    def __init__(
            self,
            connection_factory: duckdb.DuckDBPyConnection,
            query: str,
            deserializer: Any | None = None):
        super().__init__(deserializer=deserializer)

        self.connection = connection_factory
        self.query = query

    def run(self) -> None:
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        logger.debug(
            "duckdb runner (%s) started", self.study_id)

        try:
            if self.is_closed():
                logger.info(
                    "runner (%s) closed before execution",
                    self.study_id)
                self._finalize(started)
                return

            with self.connection.cursor() as cursor:
                for record in cursor.execute(self.query).fetchall():
                    val = self.deserializer(record)
                    if val is None:
                        continue
                    self.put_value_in_result_queue(val)
                    if self.is_closed():
                        logger.debug(
                            "query runner (%s) closed while iterating",
                            self.query)
                        break

        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(
                "exception in runner (%s) run",
                self.query)
            self.put_value_in_result_queue(ex)
        finally:
            logger.debug(
                "runner (%s) closing connection", self.query)

        self._finalize(started)

    def _finalize(self, started: float) -> None:
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.query, elapsed)


class DuckDbQueryDialect(Dialect):
    """Abstracts away details related to bigquery."""

    def __init__(self, ns: str | None = None):
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

    def build_table_name(
        self, table: str,
        db: str | None,  # noqa: ARG002
    ) -> str:
        return table

    def build_array_join(self, column: str, allias: str) -> str:
        return (
            f"\n    CROSS JOIN\n        "
            f"(SELECT UNNEST({column}) AS {allias})"
        )


class DuckDbVariants(SqlSchema2Variants):
    """Backend for DuckDb storage backend."""

    RUNNER_CLASS = DuckDbRunner

    def __init__(
        self,
        connection_factory: DuckDbConnectionFactory,
        db: str | None,
        family_variant_table: str | None,
        summary_allele_table: str | None,
        pedigree_table: str,
        meta_table: str,
        gene_models: GeneModels | None = None,
    ) -> None:
        self.connection_factory = connection_factory
        assert self.connection_factory is not None

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

    def _get_connection_factory(self) -> Any:
        return self.connection_factory.connect().cursor()

    def _fetch_variants_data_schema(self) -> dict[str, Any] | None:
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'variants_data_schema'
               LIMIT 1
            """  # noqa: S608

        with self._get_connection_factory() as connection:
            result = connection.execute(query).fetchall()
            for row in result:
                return cast(dict[str, Any], yaml.safe_load(row[0]))
            return None

    def _fetch_tblproperties(self) -> str:
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'partition_description'
               LIMIT 1
            """  # noqa: S608

        with self._get_connection_factory() as connection:
            result = connection.execute(query).fetchall()
            for row in result:
                return cast(str, row[0])
            return ""

    def _fetch_summary_schema(self) -> dict[str, str]:
        query = f"""SELECT value FROM {self.meta_table}
               WHERE key = 'summary_schema'
               LIMIT 1
            """  # noqa: S608

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
            """  # noqa: S608

        schema_content = ""
        with self._get_connection_factory() as connection:
            rows = connection.execute(query).fetchall()
            for row in rows:
                schema_content = row[0]
        return dict(line.split("|") for line in schema_content.split("\n"))

    def _fetch_schema(self, _table: str) -> dict[str, str]:
        return {}

    def _fetch_pedigree(self) -> pd.DataFrame:
        query = f"SELECT * FROM {self.pedigree_table}"  # noqa: S608
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
            ped_df.role = ped_df.role.apply(Role.from_value)  # type: ignore
            ped_df.sex = ped_df.sex.apply(Sex.from_value)  # type: ignore
            ped_df.status = ped_df.status.apply(
                Status.from_value)  # type: ignore
            ped_df.loc[ped_df.layout.isna(), "layout"] = None

            return ped_df

    def _deserialize_summary_variant(self, record: list[str]) -> SummaryVariant:
        return self.deserialize_summary_variant(record[2])  # type: ignore

    def _deserialize_family_variant(self, record: list[str]) -> FamilyVariant:
        return self.deserialize_family_variant(record[4], record[5])  # type: ignore
