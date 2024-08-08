import logging
import time
from typing import Any, cast

import pandas as pd
import yaml
from google.cloud import bigquery

from dae.genomic_resources.gene_models import GeneModels
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.variants.attributes import Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from gcp_storage.bigquery_query_runner import BigQueryQueryRunner

logger = logging.getLogger(__name__)


class BigQueryDialect(Dialect):
    """Abstracts away details related to bigquery."""

    def __init__(self, ns: str | None = None) -> None:
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


class BigQueryVariants(SqlSchema2Variants):
    """Backend for BigQuery."""

    RUNNER_CLASS = BigQueryQueryRunner

    def __init__(
        self,
        gcp_project_id: str,
        db: str,
        summary_allele_table: str | None,
        family_variant_table: str | None,
        pedigree_table: str,
        meta_table: str,
        gene_models: GeneModels | None = None,
    ) -> None:
        self.client = bigquery.Client(project=gcp_project_id)

        super().__init__(
            BigQueryDialect(ns=gcp_project_id),
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models)
        assert db, db
        assert pedigree_table, pedigree_table

        self.start_time = time.time()

    def _fetch_tblproperties(self) -> str:
        query = f"""SELECT value FROM {self.db}.{self.meta_table}
               WHERE key = 'partition_description'
               LIMIT 1
            """  # noqa: S608

        result = self.client.query(query).result()
        for row in result:
            return cast(str, row[0])
        return ""

    def _fetch_schema(self, table: str) -> dict[str, str]:
        query = f"""
            SELECT * FROM {self.db}.INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{table}'
        """  # noqa: S608
        df = self.client.query(query).result().to_dataframe()

        records = df[["column_name", "data_type"]].to_records()
        return {col_name: col_type for (_, col_name, col_type) in records}

    def _fetch_variants_data_schema(self) -> dict[str, Any] | None:
        query = f"""SELECT value FROM {self.db}.{self.meta_table}
               WHERE key = 'variants_data_schema'
               LIMIT 1
            """  # noqa: S608

        for row in self.client.query(query).result():
            return cast(dict[str, Any], yaml.safe_load(row[0]))
        return None

    def _fetch_pedigree(self) -> pd.DataFrame:
        query = f"SELECT * FROM {self.db}.{self.pedigree_table}"  # noqa: S608
        ped_df = self.client.query(query).result().to_dataframe()

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
        return ped_df.sort_values(by=["family_id", "member_index"])

    def _get_connection_factory(self) -> Any:
        # pylint: disable=protected-access
        return self.client

    def _deserialize_summary_variant(
        self, record: Any,
    ) -> SummaryVariant:
        return self.deserialize_summary_variant(record.summary_variant_data)

    def _deserialize_family_variant(
        self, record: Any,
    ) -> FamilyVariant:
        return self.deserialize_family_variant(
            record.summary_variant_data,
            record.family_variant_data,
        )
