import logging
from typing import Optional
import pandas as pd
from dae.query_variants.sql.schema2.base_query_builder import \
    BaseQueryBuilder, Dialect,\
    TableSchema

logger = logging.getLogger(__name__)


class FamilyQueryBuilder(BaseQueryBuilder):
    """Build queries related to family variants."""

    def __init__(
        self,
        dialect: Dialect,
        db: str,
        family_variant_table: str,
        summary_allele_table: str,
        pedigree_table: str,
        family_variant_schema: TableSchema,
        summary_allele_schema: TableSchema,
        table_properties: Optional[dict],
        pedigree_schema: TableSchema,
        pedigree_df: pd.DataFrame,
        gene_models=None,
        do_join_pedigree=False,
        do_join_allele_in_members=False
    ):
        # pylint: disable=too-many-arguments
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table

        super().__init__(
            dialect,
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            family_variant_schema,
            summary_allele_schema,
            table_properties,
            pedigree_schema,
            pedigree_df,
            gene_models=gene_models,
        )

        self.do_join_pedigree = do_join_pedigree
        self.do_join_allele_in_members = do_join_allele_in_members

    def _query_columns(self):
        self.select_accessors = {
            "bucket_index": "sa.bucket_index",
            "summary_index": "sa.summary_index",
            "family_index": "fa.family_index",
            "family_id": "fa.family_id",
            "summary_variant_data": "sa.summary_variant_data",
            "family_variant_data": "fa.family_variant_data",
        }

        columns = list(self.select_accessors.values())
        return columns

    def _build_join(self, genes=None, effect_types=None):

        if self.do_join_allele_in_members or self.do_join_pedigree:
            self._add_to_product(
                self.dialect.build_array_join("fa.allele_in_members", "pi"))
            # inner = "fa.allele_in_members"
            # if self.dialect.add_unnest_in_join():
            #     inner = f"UNNEST({inner})"
            # self._add_to_product(f"\n    JOIN\n    {inner} AS pi")

        if self.do_join_pedigree:
            pedigree_table = self.dialect.build_table_name(
                self.pedigree_table, self.db)
            pi_ref = "pi" + self.dialect.array_item_suffix()
            self._add_to_product(f"\n    JOIN"
                                 f"\n    {pedigree_table} AS pedigree"
                                 f"\n    ON ({pi_ref} = pedigree.person_id)")

        if genes is not None or effect_types is not None:
            self._add_to_product(
                self.dialect.build_array_join("sa.effect_gene", "eg")
            )
            # inner_clause = (
            #     "UNNEST(sa.effect_gene)"
            #     if self.dialect.add_unnest_in_join()
            #     else "sa.effect_gene"
            # )
            # self._add_to_product(f"\n    JOIN\n    {inner_clause} AS eg")

    def _build_from(self):
        summary_table_name = self.dialect.build_table_name(
            self.summary_allele_table, self.db)
        assert self.family_variant_table is not None
        family_table_name = self.dialect.build_table_name(
            self.family_variant_table, self.db)
        self._add_to_product(
            f"\n  FROM"
            f"\n    {summary_table_name} AS sa"
            f"\n    JOIN"
            f"\n    {family_table_name} AS fa"
            f"\n    ON (fa.summary_index = sa.summary_index AND"
            f"\n        fa.bucket_index = sa.bucket_index AND"
            f"\n        fa.allele_index = sa.allele_index)")

    def _build_group_by(self):
        pass

    def _build_having(self, **kwargs):
        pass
