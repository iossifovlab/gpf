import logging
from dae.backends.impala.base_query_builder import BaseQueryBuilder

logger = logging.getLogger(__name__)


class SummaryVariantsQueryBuilder(BaseQueryBuilder):
    def __init__(
            self, db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, gene_models=None):
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
        self.select_accessors = {
            "bucket_index": "variants.bucket_index",
            "summary_index": "variants.summary_index",
            "variant_data": "MIN(variants.variant_data)",
            "family_variants_count": "COUNT(DISTINCT variants.family_id)",
            "seen_in_status": "gpf_or(pedigree.status)",
            "seen_in_denovo":
                "gpf_bit_or(BITAND(inheritance_in_members, 4))",
            "extra_attributes": "MIN(variants.extra_attributes)"
        }
        columns = [
            "variants.bucket_index",
            "variants.summary_index",
            "MIN(variants.variant_data)",
            "COUNT(DISTINCT variants.family_id)",
            "gpf_or(pedigree.status)",
            "gpf_bit_or(BITAND(inheritance_in_members, 4))"
        ]
        if self.has_extra_attributes:
            columns.append("MIN(variants.extra_attributes)")

        return columns

    def build_from(self):
        from_clause = f"FROM {self.db}.{self.variants_table} as variants"
        self._add_to_product(from_clause)

    def build_join(self):
        join_clause = f"JOIN {self.db}.{self.pedigree_table} as pedigree"
        self._add_to_product(join_clause)

    def build_group_by(self):
        self._add_to_product("GROUP BY bucket_index, summary_index")

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
    ):
        super().build_where(
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
        in_members = "AND variants.variant_in_members = pedigree.person_id"
        self._add_to_product(in_members)

    def create_row_deserializer(self, serializer):
        def deserialize_row(row):
            cols = dict()
            for idx, col_name in enumerate(self.query_columns):
                cols[col_name] = row[idx]

            bucket_index = cols[self.select_accessors["bucket_index"]]
            summary_index = cols[self.select_accessors["summary_index"]]
            variant_data = cols[self.select_accessors["variant_data"]]
            print(row)
            family_variants_count = cols[
                self.select_accessors["family_variants_count"]]
            seen_in_status = cols[self.select_accessors["seen_in_status"]]
            seen_in_denovo = cols[self.select_accessors["seen_in_denovo"]]
            extra_attributes = cols.get(
                self.select_accessors["extra_attributes"], None)

            if type(variant_data) == str:
                logger.debug(
                    f"variant_data is string!!!! "
                    f"{bucket_index}, {summary_index}"
                )
                variant_data = bytes(variant_data, "utf8")
            if type(extra_attributes) == str:
                logger.debug(
                    f"extra_attributes is string!!!! "
                    f"{bucket_index}, {summary_index}"
                )
                extra_attributes = bytes(extra_attributes, "utf8")

            v = serializer.deserialize_summary_variant(
                variant_data, extra_attributes
            )
            if v is not None:
                v.update_attributes({
                    "family_variants_count": [family_variants_count],
                    "seen_in_status": [seen_in_status],
                    "seen_in_denovo": [seen_in_denovo]
                })

            return v

        return deserialize_row
