import json
import logging
from contextlib import closing
from typing import Optional, Any, cast


import numpy as np
import pandas as pd
from sqlalchemy import pool

from impala.util import as_pandas
from dae.query_variants.query_runners import QueryRunner
from dae.variants.attributes import Role, Status, Sex, Inheritance
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.variants.variant import SummaryVariantFactory, SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.genomic_resources.gene_models import GeneModels

from impala2_storage.helpers.impala_query_runner import ImpalaQueryRunner
from impala2_storage.helpers.impala_helpers import ImpalaHelpers

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
        family_variant_table: str,
        summary_allele_table: str,
        pedigree_table: str,
        meta_table: str,
        gene_models: Optional[GeneModels] = None,
    ) -> None:
        self._impala_helpers = impala_helpers
        super().__init__(
            ImpalaDialect(),
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models)

    def connection(self) -> pool.PoolProxiedConnection:
        conn = self._impala_helpers.connection()
        logger.debug(
            "getting connection to host %s from impala helpers %s",
            conn.host, id(self._impala_helpers)  # type: ignore
        )
        return conn

    def _fetch_schema(self, table: str) -> dict[str, str]:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"""DESCRIBE {self.db}.{table}"""
                cursor.execute(query)
                df = as_pandas(cursor)
            records = df[["name", "type"]].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return schema

    def _fetch_tblproperties(self) -> str:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"""SELECT value FROM {self.db}.{self.meta_table}
                            WHERE key = 'partition_description'
                            LIMIT 1
                """

                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    return str(row[0])
        return ""

    def _fetch_pedigree(self) -> pd.DataFrame:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"""SELECT * FROM {self.db}.{self.pedigree_table}"""
                cursor.execute(query)
                ped_df = cast(pd.DataFrame, as_pandas(cursor))

        ped_df.role = ped_df.role.apply(Role)  # type: ignore
        ped_df.sex = ped_df.sex.apply(Sex)  # type: ignore
        ped_df.status = ped_df.status.apply(Status)  # type: ignore

        return ped_df

    def _get_connection_factory(self) -> Any:
        # pylint: disable=protected-access
        return self._impala_helpers._connection_pool

    def _deserialize_summary_variant(self, record: tuple) -> SummaryVariant:
        sv_record = json.loads(record[-1])
        return SummaryVariantFactory.summary_variant_from_records(sv_record)

    def _deserialize_family_variant(self, record: tuple) -> FamilyVariant:
        sv_record = json.loads(record[-2])
        fv_record = json.loads(record[-1])
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
