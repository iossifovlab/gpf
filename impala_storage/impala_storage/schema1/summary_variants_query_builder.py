import logging
from collections.abc import Iterable
from typing import Any, Callable, Dict, List

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.genomic_resources.gene_models import GeneModels
from dae.pedigrees.families_data import FamiliesData
from dae.utils.regions import Region
from dae.variants.variant import SummaryVariant
from impala_storage.schema1.base_query_builder import (
    BaseQueryBuilder,
    RealAttrFilterType,
)
from impala_storage.schema1.serializers import AlleleParquetSerializer

logger = logging.getLogger(__name__)


class SummaryVariantsQueryBuilder(BaseQueryBuilder):
    """Build queries related to summary variants."""

    def __init__(
        self, db: str, variants_table: str, pedigree_table: str,
        variants_schema: List[AttributeInfo],
        table_properties: dict[str, Any],
        pedigree_schema: dict[str, str],
        families: FamiliesData,
        gene_models: GeneModels | None = None,
        summary_variants_table: str | None = None,
    ) -> None:
        self.summary_variants_table = summary_variants_table
        super().__init__(
            db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            families, gene_models=gene_models)

    def _where_accessors(self) -> Dict[str, str]:
        accessors = super()._where_accessors()

        for key, value in accessors.items():
            accessors[key] = f"variants.{value}"
        return accessors

    def _query_columns(self) -> List[str]:
        if self.summary_variants_table:
            self.select_accessors = {
                "bucket_index": "variants.bucket_index",
                "summary_index": "variants.summary_index",
                "variant_data": "variants.variant_data",
                "family_variants_count": "variants.family_variants_count",
                "seen_in_status": "variants.seen_in_status",
                "seen_as_denovo": "variants.seen_as_denovo",
            }
            # if self.has_extra_attributes:
            #     self.select_accessors["extra_attributes"] = \
            #         "MIN(variants.extra_attributes)"
        else:
            self.select_accessors = {
                "bucket_index": "variants.bucket_index",
                "summary_index": "variants.summary_index",
                "variant_data": "MIN(variants.variant_data)",
                "family_variants_count": "COUNT(DISTINCT variants.family_id)",
                "seen_in_status": "gpf_bit_or(pedigree.status)",
                "seen_as_denovo":
                    "gpf_or(BITAND(inheritance_in_members, 4))",
            }
            if self.has_extra_attributes:
                self.select_accessors["extra_attributes"] = \
                    "MIN(variants.extra_attributes)"

        columns = list(self.select_accessors.values())

        return columns

    def build_from(self) -> None:
        table = self.summary_variants_table \
            if self.summary_variants_table is not None \
            else self.variants_table
        from_clause = f"FROM {self.db}.{table} as variants"
        self._add_to_product(from_clause)

    def build_join(self) -> None:
        if self.summary_variants_table is not None:
            return
        join_clause = f"JOIN {self.db}.{self.pedigree_table} as pedigree"
        self._add_to_product(join_clause)

    def build_group_by(self) -> None:
        if self.summary_variants_table is not None:
            return

        self._add_to_product(
            "GROUP BY bucket_index, summary_index, "
            "allele_index, variant_type, transmission_type")

    def build_where(
        self,
        regions: List[Region] | None = None,
        genes: List[str] | None = None,
        effect_types: List[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: List[str] | str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        **_kwargs: Any,
    ) -> None:
        # FIXME too many arguments
        # pylint: disable=too-many-arguments
        if self.summary_variants_table:
            inheritance = None
        where_clause = self._base_build_where(
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

        if self.summary_variants_table is not None:
            return

        if where_clause:
            in_members = "AND variants.variant_in_members = pedigree.person_id"
        else:
            in_members = \
                "WHERE variants.variant_in_members = pedigree.person_id"
        self._add_to_product(in_members)

    def create_row_deserializer(
        self, serializer: AlleleParquetSerializer,
    ) -> Callable:
        def deserialize_row(row: tuple) -> SummaryVariant:
            cols = {}
            for idx, col_name in enumerate(self.query_columns):
                cols[col_name] = row[idx]

            bucket_index = cols[self.select_accessors["bucket_index"]]
            summary_index = cols[self.select_accessors["summary_index"]]
            variant_data = cols[self.select_accessors["variant_data"]]
            family_variants_count = cols[
                self.select_accessors["family_variants_count"]]
            seen_in_status = cols[self.select_accessors["seen_in_status"]]
            seen_as_denovo = cols[self.select_accessors["seen_as_denovo"]]

            extra_attributes = None
            if "extra_attributes" in self.select_accessors:
                extra_attributes = cols.get(
                    self.select_accessors["extra_attributes"], None)

            if isinstance(variant_data, str):
                logger.debug(
                    "variant_data is string!!!! %d, %s",
                    bucket_index, summary_index,
                )
                variant_data = bytes(variant_data, "utf8")
            if isinstance(extra_attributes, str):
                # TODO do we really need that if. Looks like a python2 leftover
                # logger.debug(
                #     f"extra_attributes is string!!!! "
                #     f"{bucket_index}, {summary_index}"
                # )
                extra_attributes = bytes(extra_attributes, "utf8")

            v = serializer.deserialize_summary_variant(
                variant_data, extra_attributes,
            )
            if v is not None:
                v.update_attributes({
                    "family_variants_count": [family_variants_count],
                    "seen_in_status": [seen_in_status],
                    "seen_as_denovo": [seen_as_denovo],
                })

            return v

        return deserialize_row
