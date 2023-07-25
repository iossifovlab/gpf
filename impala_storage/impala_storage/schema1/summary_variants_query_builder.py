import logging
from impala_storage.schema1.base_query_builder import BaseQueryBuilder

logger = logging.getLogger(__name__)


class SummaryVariantsQueryBuilder(BaseQueryBuilder):
    """Build queries related to summary variants."""

    def __init__(
            self, db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, gene_models=None, summary_variants_table=None):
        self.summary_variants_table = summary_variants_table
        super().__init__(
            db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, gene_models=gene_models)

    def _where_accessors(self):
        accessors = super()._where_accessors()

        for key, value in accessors.items():
            accessors[key] = f"variants.{value}"
        return accessors

    def _query_columns(self):
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

    def build_from(self):
        table = self.summary_variants_table \
            if self.summary_variants_table is not None \
            else self.variants_table
        from_clause = f"FROM {self.db}.{table} as variants"
        self._add_to_product(from_clause)

    def build_join(self):
        if self.summary_variants_table is not None:
            return
        join_clause = f"JOIN {self.db}.{self.pedigree_table} as pedigree"
        self._add_to_product(join_clause)

    def build_group_by(self):
        if self.summary_variants_table is not None:
            return

        self._add_to_product(
            "GROUP BY bucket_index, summary_index, "
            "allele_index, variant_type, transmission_type")

    def build_where(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            **_kwargs):
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

    def create_row_deserializer(self, serializer):
        def deserialize_row(row):
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
            extra_attributes = cols.get(
                self.select_accessors.get("extra_attributes", None), None)

            if isinstance(variant_data, str):
                logger.debug(
                    "variant_data is string!!!! %d, %s",
                    bucket_index, summary_index
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
                variant_data, extra_attributes
            )
            if v is not None:
                v.update_attributes({
                    "family_variants_count": [family_variants_count],
                    "seen_in_status": [seen_in_status],
                    "seen_as_denovo": [seen_as_denovo]
                })

            return v

        return deserialize_row
