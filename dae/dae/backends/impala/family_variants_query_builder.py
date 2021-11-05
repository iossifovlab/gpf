import logging
from dae.backends.impala.base_query_builder import BaseQueryBuilder
from dae.variants.attributes import Status, Role, Sex

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

    def _get_pedigree_column_value(self, source, str_value):
        if source == "status":
            value = Status.from_name(str_value).value
        elif source == "role":
            value = Role.from_name(str_value).value
        elif source == "sex":
            value = Sex.from_name(str_value).value
        else:
            value = str_value
        return value

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
            "variant_data": "variants.variant_data",
        }
        if self.has_extra_attributes:
            self.select_accessors["extra_attributes"] = \
                "variants.extra_attributes"
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
        pedigree_fields=None
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

        if pedigree_fields is not None:
            if where_clause:
                pedigree_where = "AND ("
            else:
                pedigree_where = "WHERE ("

            first_or = True

            for field in pedigree_fields.values():
                if not first_or:
                    pedigree_where += "OR "
                values = field["values"]
                sources = field["sources"]
                first_and = True
                pedigree_where += "("
                for source, str_value in zip(sources, values):
                    if not first_and:
                        pedigree_where += "AND "
                    value = self._get_pedigree_column_value(source, str_value)
                    pedigree_where += f"pedigree.{source} = {value} "
                    first_and = False
                pedigree_where += ")"
            pedigree_where += ")"

            self._add_to_product(pedigree_where)

        if where_clause:
            in_members = "AND variants.variant_in_members = pedigree.person_id"
        else:
            in_members = \
                "WHERE variants.variant_in_members = pedigree.person_id"
        self._add_to_product(in_members)

    def build_group_by(self):
        pass

    def build_having(self, **kwargs):
        pass

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
