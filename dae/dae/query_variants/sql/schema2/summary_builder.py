import logging
from collections.abc import Iterable
from typing import Any

from dae.genomic_resources.gene_models import GeneModels
from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.sql.schema2.base_query_builder import (
    BaseQueryBuilder,
    Dialect,
    TableSchema,
)
from dae.utils.regions import Region

logger = logging.getLogger(__name__)
RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]


class SummaryQueryBuilder(BaseQueryBuilder):
    """Build queries related to summary variants."""

    def __init__(
        self,
        dialect: Dialect,
        db: str | None,
        family_variant_table: str | None,
        summary_allele_table: str,
        pedigree_table: str,
        family_variant_schema: TableSchema,
        summary_allele_schema: TableSchema,
        table_properties: dict | None,
        pedigree_schema: TableSchema,
        families: FamiliesData,
        gene_models: GeneModels | None = None,
    ):
        # pylint: disable=too-many-arguments
        super().__init__(
            dialect,
            db,
            None,                      # family_variant_table,
            summary_allele_table,
            pedigree_table,
            None,                      # family_variant_schema,
            summary_allele_schema,
            table_properties,
            pedigree_schema,
            families,
            gene_models=gene_models,
        )

    def _query_columns(self) -> list[str]:
        return [
            "sa.bucket_index",
            "sa.summary_index",
            "sa.summary_variant_data",
        ]

    def _build_from(self) -> None:
        summary_table_name = self.dialect.build_table_name(
            self.summary_allele_table, self.db)
        from_clause = f"\n  FROM\n    {summary_table_name} AS sa"
        self._add_to_product(from_clause)

    def _build_join(
        self, genes: list[str] | None = None,
        effect_types: list[str] | None = None,
    ) -> None:
        if genes is not None or effect_types is not None:
            self._add_to_product(
                self.dialect.build_array_join("sa.effect_gene", "eg"))

    def _build_group_by(self) -> None:
        pass

    def _build_having(self, **kwargs: Any) -> None:
        pass

    def _build_where(
        self,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: str | list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        pedigree_fields: tuple | None = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=too-many-arguments,too-many-locals,unused-argument
        inheritance = None
        person_ids = None
        family_ids = None
        roles = None
        sexes = None

        where_clause = self._build_where_string(
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
        )
        self._add_to_product(where_clause)
