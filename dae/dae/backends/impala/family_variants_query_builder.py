import logging
from dae.backends.impala.base_query_builder import BaseQueryBuilder

logger = logging.getLogger(__name__)


class FamilyVariantsQueryBuilder(BaseQueryBuilder):
    def __init__(
            self, db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, families, gene_models=None, do_join=False):
        self.do_join = do_join
        super().__init__(
            db, variants_table, pedigree_table,
            variants_schema, table_properties, pedigree_schema,
            pedigree_df, gene_models=gene_models)
        self.families = families

    def _query_columns(self):
        self.select_accessors = {
            "bucket_index": "variants.bucket_index",
            "summary_index": "variants.summary_index",
            "chromosome": "MIN(variants.chromosome)",
            "`position`": "MIN(variants.`position`)",
            "end_position": "MIN(variants.end_position)",
            "variant_type": "MIN(variants.variant_type)",
            "reference": "MIN(variants.reference)",
            "family_id": "variants.family_id",
            "variant_data": "MIN(variants.variant_data)",
        }
        if self.has_extra_attributes:
            self.select_accessors["extra_attributes"] = \
                "min(variants.extra_attributes)"
        if not self.do_join:
            for k, v in self.select_accessors.items():
                self.select_accessors[k] = k
        columns = list(self.select_accessors.values())

        return columns

    def _where_accessors(self):
        accessors = super()._where_accessors()

        if self.do_join:
            for key, value in accessors.items():
                accessors[key] = f"variants.{value}"
        return accessors

    def build_from(self):
        if self.do_join:
            from_clause = f"FROM {self.db}.{self.variants_table} as variants"
        else:
            from_clause = f"FROM {self.db}.{self.variants_table}"
        self._add_to_product(from_clause)

    def build_join(self):
        if not self.do_join:
            return
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
        if not self.do_join:
            return
        if where_clause:
            in_members = "AND variants.variant_in_members = pedigree.person_id"
        else:
            in_members = \
                "WHERE variants.variant_in_members = pedigree.person_id"
        self._add_to_product(in_members)

    def build_group_by(self):
        if not self.do_join:
            return
        group_by_clause = (
            "GROUP BY variants.bucket_index, "
            "variants.summary_index, variants.family_id"
        )
        self._add_to_product(group_by_clause)

    def build_having(self, **kwargs):
        if not self.do_join:
            return
        affected_status = kwargs["affected_status"]
        statuses = set()
        if affected_status is not None and len(affected_status):
            statuses = set()
            for status in affected_status:
                if status == "affected only":
                    statuses.add("2")
                elif status == "unaffected only":
                    statuses.add("1"),
                elif status == "affected and unaffected":
                    statuses.add("3")
        in_clause = f"IN ({', '.join(statuses)})"
        having_clause = f"HAVING gpf_bit_or(pedigree.status) {in_clause}"
        self._add_to_product(having_clause)

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
            variant_data = cols[self.select_accessors["variant_data"]]
            extra_attributes = cols.get(
                self.select_accessors.get("extra_attributes", None), None)

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
                # logger.debug(
                #     f"extra_attributes is string!!!! "
                #     f"{family_id}, {chrom}, "
                #     f"{position}, {end_position}, {reference}")
                extra_attributes = bytes(extra_attributes, "utf8")

            family = self.families[family_id]
            v = serializer.deserialize_family_variant(
                variant_data, family, extra_attributes
            )
            return v
        return deserialize_row
