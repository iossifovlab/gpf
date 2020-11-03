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
        self.select_accessors = {
            "bucket_index": "variants.bucket_index",
            "summary_index": "variants.summary_index",
            "chromosome": "variants.chromosome",
            "`position`": "variants.`position`",
            "end_position": "variants.end_position",
            "variant_type": "variants.variant_type",
            "reference": "variants.reference",
            "family_id": "variants.family_id",
            "seen_in_status": "pedigree.status",
            "variant_data": "variants.variant_data",
        }
        if self.has_extra_attributes:
            self.select_accessors["extra_attributes"] = \
                "variants.extra_attributes"
        columns = list(self.select_accessors.values())

        return columns

    def build_from(self):
        from_clause = f"FROM {self.db}.{self.variants_table} as variants"
        self._add_to_product(from_clause)

    def build_group_by(self):
        pass

    def build_join(self):
        join_clause = f"JOIN {self.db}.{self.pedigree_table} as pedigree"
        self._add_to_product(join_clause)

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
        affected_status=None,
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
        if affected_status is not None and len(affected_status):
            statuses = set()
            for status in affected_status:
                if status == "affected only":
                    statuses.add("2")
                elif status == "unaffected only":
                    statuses.add("1"),
                elif status == "affected and unaffected":
                    statuses.add("1")
                    statuses.add("2")

            status = f"AND pedigree.status IN ({','.join(statuses)})"
            self._add_to_product(status)

    def create_row_deserializer(self, serializer):
        seen = set()

        def deserialize_row(row):
            cols = dict()
            for idx, col_name in enumerate(self.query_columns):
                cols[col_name] = row[idx]

            bucket_index = cols[self.select_accessors["bucket_index"]]
            summary_index = cols[self.select_accessors["summary_index"]]
            family_id = cols[self.select_accessors["family_id"]]
            chrom = cols[self.select_accessors["chromosome"]]
            position = cols[self.select_accessors["`position`"]]
            end_position = cols[self.select_accessors["end_position"]]
            reference = cols[self.select_accessors["reference"]]
            seen_in_status = cols[self.select_accessors["seen_in_status"]]
            variant_data = cols[self.select_accessors["variant_data"]]
            extra_attributes = cols.get(
                self.select_accessors.get("extra_attributes", None), None)

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
            if v is not None:
                v.update_attributes({
                    "seen_in_status": [seen_in_status]
                })
            return v
        return deserialize_row
