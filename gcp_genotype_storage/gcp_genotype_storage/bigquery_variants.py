import time
import json
import logging
from typing import Optional, Any

import numpy as np

from google.cloud import bigquery

from dae.variants.attributes import Role, Status, Sex
from dae.query_variants.sql.schema2.base_variants import SqlSchema2Variants
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from gcp_genotype_storage.bigquery_query_runner import BigQueryQueryRunner

logger = logging.getLogger(__name__)


class BigQueryDialect(Dialect):
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


class BigQueryVariants(SqlSchema2Variants):
    """Backend for BigQuery."""

    RUNNER_CLASS = BigQueryQueryRunner

    def __init__(
        self,
        gcp_project_id,
        db,
        summary_allele_table,
        family_variant_table,
        pedigree_table,
        meta_table,
        gene_models=None,
    ):
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

    def _fetch_tblproperties(self):
        query = f"""SELECT value FROM {self.db}.{self.meta_table}
               WHERE key = 'partition_description'
               LIMIT 1
            """

        result = self.client.query(query).result()
        for row in result:
            return row[0]
        return ""

    def _fetch_schema(self, table):
        query = f"""
            SELECT * FROM {self.db}.INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{table}'
        """
        df = self.client.query(query).result().to_dataframe()

        records = df[["column_name", "data_type"]].to_records()
        schema = {col_name: col_type for (_, col_name, col_type) in records}
        return schema

    def _fetch_pedigree(self):
        query = f"SELECT * FROM {self.db}.{self.pedigree_table}"

        # ped_df = pandas_gbq.read_gbq(q, project_id=self.gcp_project_id)
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

        return ped_df

    def _get_connection_factory(self) -> Any:
        # pylint: disable=protected-access
        return self.client

    def _deserialize_summary_variant(self, record):
        sv_record = json.loads(record.summary_variant_data)
        return SummaryVariantFactory.summary_variant_from_records(
            sv_record
        )

    def _deserialize_family_variant(self, record):
        sv_record = json.loads(record.summary_variant_data)
        fv_record = json.loads(record.family_variant_data)

        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
        )
