import logging
from dae.backends.impala.base_query_builder import BaseQueryBuilder

logger = logging.getLogger(__name__)


class FamilyVariantsQueryBuilder(BaseQueryBuilder):
    def __init__(
            self, db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, families, gene_models=None):
        super().__init__(
            db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, gene_models=gene_models)
        self.families = families

    def _query_columns(self):
        columns = [
            "bucket_index",
            "summary_index",
            "chromosome",
            "`position`",
            "end_position",
            "variant_type",
            "reference",
            "family_id",
            "variant_data",
        ]
        if self.has_extra_attributes:
            columns.append("extra_attributes")

        return columns

    def build_group_by(self):
        pass

    def build_join(self):
        pass

    def create_row_deserializer(self, serializer):
        seen = set()

        def deserialize_row(row):
            cols = dict()
            for idx, col_name in enumerate(self.query_columns):
                cols[col_name] = row[idx]

            bucket_index = cols["bucket_index"]
            summary_index = cols["summary_index"]
            family_id = cols["family_id"]
            chrom = cols["chromosome"]
            position = cols["`position`"]
            end_position = cols["end_position"]
            reference = cols["reference"]
            variant_data = cols["variant_data"]
            extra_attributes = cols.get("extra_attributes", None)

            # FIXME:
            # fvuid = f"{bucket_index}:{summary_index}:{family_index}"
            fvuid = f"{bucket_index}:{summary_index}:{family_id}"
            if fvuid in seen:
                return None
            seen.add(fvuid)

            if type(variant_data) == str:
                logger.debug(
                    f"variant_data is string!!!! "
                    f"{family_id}, {chrom}, "
                    f"{position}, {end_position}, {reference}")
                variant_data = bytes(variant_data, "utf8")
            if type(extra_attributes) == str:
                logger.debug(
                    f"extra_attributes is string!!!! "
                    f"{family_id}, {chrom}, "
                    f"{position}, {end_position}, {reference}")
                extra_attributes = bytes(extra_attributes, "utf8")

            family = self.families[family_id]
            v = serializer.deserialize_family_variant(
                variant_data, family, extra_attributes
            )
            return v
        return deserialize_row
