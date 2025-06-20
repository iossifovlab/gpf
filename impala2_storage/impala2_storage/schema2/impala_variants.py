import logging
from contextlib import closing
from typing import Any, cast

import pandas as pd
import yaml
from dae.genomic_resources.gene_models import GeneModels
from dae.query_variants.query_runners import QueryRunner
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.variants.attributes import Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from impala.util import as_pandas
from sqlalchemy import pool

from impala2_storage.helpers.impala_helpers import ImpalaHelpers
from impala2_storage.helpers.impala_query_runner import ImpalaQueryRunner

logger = logging.getLogger(__name__)


class ImpalaDialect(Dialect):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def escape_char() -> str:
        return "`"


class ImpalaVariants(SqlSchema2Variants):
    """A backend implementing an impala backend."""

    RUNNER_CLASS: type[QueryRunner] = ImpalaQueryRunner

    def __init__(
        self,
        impala_helpers: ImpalaHelpers,
        db: str,
        family_variant_table: str | None,
        summary_allele_table: str | None,
        pedigree_table: str,
        meta_table: str,
        gene_models: GeneModels | None = None,
    ) -> None:
        self._impala_helpers = impala_helpers
        super().__init__(
            ImpalaDialect(),
            db,
            family_variant_table=family_variant_table,
            summary_allele_table=summary_allele_table,
            pedigree_table=pedigree_table,
            meta_table=meta_table,
            gene_models=gene_models)

    def connection(self) -> pool.PoolProxiedConnection:
        conn = self._impala_helpers.connection()
        logger.debug(
            "getting connection to host %s from impala helpers %s",
            conn.host, id(self._impala_helpers),  # type: ignore
        )
        return conn

    def _fetch_schema(self, table: str) -> dict[str, str]:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"""DESCRIBE {self.db}.{table}"""
                cursor.execute(query)
                df = as_pandas(cursor)
            records = df[["name", "type"]].to_records()
            return {
                col_name: col_type for (_, col_name, col_type) in records
            }

    def _fetch_tblproperties(self) -> str:
        with closing(self.connection()) as conn, \
                closing(conn.cursor()) as cursor:
            query = f"""SELECT value FROM {self.db}.{self.meta_table}
                        WHERE key = 'partition_description'
                        LIMIT 1
            """  # noqa: S608

            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                return str(row[0])
        return ""

    def _fetch_variants_blob_serializer(self) -> str:
        with closing(self.connection()) as conn, \
                closing(conn.cursor()) as cursor:
            query = f"""SELECT value FROM {self.db}.{self.meta_table}
                        WHERE key = 'variants_blob_serializer'
                        LIMIT 1
            """  # noqa: S608

            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                return str(row[0])
        return "json"

    def _fetch_variants_data_schema(self) -> dict[str, Any] | None:
        query = f"""SELECT value FROM {self.db}.{self.meta_table}
               WHERE key = 'variants_data_schema'
               LIMIT 1
            """  # noqa: S608

        with closing(self.connection()) as conn, \
                closing(conn.cursor()) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            for row in result:
                return cast(dict[str, Any], yaml.safe_load(row[0]))
            return None

    def _fetch_pedigree(self) -> pd.DataFrame:
        with closing(self.connection()) as conn, \
                closing(conn.cursor()) as cursor:
            query = f"""
                SELECT * FROM {self.db}.{self.pedigree_table}
            """  # noqa: S608
            cursor.execute(query)
            ped_df = cast(pd.DataFrame, as_pandas(cursor))

        ped_df.role = ped_df.role.apply(Role.from_value)  # type: ignore
        ped_df.sex = ped_df.sex.apply(Sex.from_value)  # type: ignore
        ped_df.status = ped_df.status.apply(Status.from_value)  # type: ignore

        return ped_df

    def _get_connection_factory(self) -> Any:
        # pylint: disable=protected-access
        return self._impala_helpers._connection_pool  # noqa: SLF001

    def _deserialize_summary_variant(self, record: tuple) -> SummaryVariant:
        return self.deserialize_summary_variant(record[-1])

    def _deserialize_family_variant(self, record: tuple) -> FamilyVariant:
        return self.deserialize_family_variant(record[-2], record[-1])
