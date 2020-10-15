import logging
from dae.backends.impala.base_query_builder import BaseQueryBuilder

logger = logging.getLogger(__name__)


class SummaryVariantsQueryBuilder(BaseQueryBuilder):
    def __init__(
            self, db, table_name, schema,
            table_properties, pedigree_schema,
            pedigree_df, gene_models=None):
        super().__init__(
            db, table_name, schema,
            table_properties, pedigree_schema,
            pedigree_df, gene_models=gene_models)

    def _query_columns(self):
        columns = [
            "bucket_index",
            "summary_index",
            "MIN(variant_data)",
            "COUNT(DISTINCT family_id)"
        ]
        if self.has_extra_attributes:
            columns.append("MIN(extra_attributes)")

        return columns

    def build_group_by(self):
        self._add_to_product("GROUP BY bucket_index, summary_index")

    def create_row_deserializer(self, serializer):
        def deserialize_row(row):
            cols = dict()
            for idx, col_name in enumerate(self.query_columns):
                cols[col_name] = row[idx]

            bucket_index = cols["bucket_index"]
            summary_index = cols["summary_index"]
            variant_data = cols["MIN(variant_data)"]
            family_variants_count = cols["COUNT(DISTINCT family_id)"]
            extra_attributes = cols.get("MIN(extra_attributes)", None)

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
                v.update_attributes(
                    {"family_variants_count": [family_variants_count]})

            return v

        return deserialize_row
