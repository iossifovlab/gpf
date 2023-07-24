import json
import logging
from contextlib import closing
from typing import Any
import numpy as np
from impala.util import as_pandas
from dae.query_variants.query_runners import QueryRunner
from dae.variants.attributes import Role, Status, Sex
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

from impala_storage.helpers.impala_query_runner import ImpalaQueryRunner

logger = logging.getLogger(__name__)


class ImpalaDialect(Dialect):
    def __init__(self):
        super().__init__()

    @staticmethod
    def escape_char() -> str:
        return "`"


class ImpalaVariants(SqlSchema2Variants):
    """A backend implementing an impala backend."""

    RUNNER_CLASS: type[QueryRunner] = ImpalaQueryRunner

    def __init__(
        self,
        impala_helpers,
        db,
        family_variant_table,
        summary_allele_table,
        pedigree_table,
        meta_table,
        gene_models=None,
    ):
        self._impala_helpers = impala_helpers
        super().__init__(
            ImpalaDialect(),
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models)

    def connection(self):
        conn = self._impala_helpers.connection()
        logger.debug(
            "getting connection to host %s from impala helpers %s",
            conn.host, id(self._impala_helpers)
        )
        return conn

    def _fetch_schema(self, table) -> dict[str, str]:
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
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
            with conn.cursor() as cursor:
                query = f"""SELECT value FROM {self.db}.{self.meta_table}
                            WHERE key = 'partition_description'
                            LIMIT 1
                """

                cursor.execute(query)

                for row in cursor:
                    return str(row[0])
        return ""

    def _fetch_pedigree(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""SELECT * FROM {self.db}.{self.pedigree_table}"""
                cursor.execute(query)
                ped_df = as_pandas(cursor)

        ped_df.role = ped_df.role.apply(Role)
        ped_df.sex = ped_df.sex.apply(Sex)
        ped_df.status = ped_df.status.apply(Status)

        return ped_df

    def _get_connection_factory(self) -> Any:
        # pylint: disable=protected-access
        return self._impala_helpers._connection_pool

    def _deserialize_summary_variant(self, record):
        sv_record = json.loads(record[-1])
        return SummaryVariantFactory.summary_variant_from_records(sv_record)

    def _deserialize_family_variant(self, record):
        sv_record = json.loads(record[-2])
        fv_record = json.loads(record[-1])

        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
        )
