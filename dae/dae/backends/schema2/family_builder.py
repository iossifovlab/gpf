import logging
from dae.backends.schema2.base_query_builder import BaseQueryBuilder, Dialect

logger = logging.getLogger(__name__)


class FamilyQueryBuilder(BaseQueryBuilder):
    """Build queries related to family variants"""

    def __init__(
        self,
        dialect: Dialect,
        db,
        family_variant_table,
        summary_allele_table,
        pedigree_table,
        family_variant_schema,
        summary_allele_schema,
        table_properties,
        pedigree_schema,
        pedigree_df,
        families,
        gene_models=None,
        do_join_affected=False,
    ):
        #pylint: disable=too-many-arguments
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

        self.do_join_affected = do_join_affected
        self.families = families

    def _query_columns(self):
        self.select_accessors = {
            "bucket_index": "sa.bucket_index",
            "summary_index": "sa.summary_index",
            "family_index": "fa.family_index",
            "family_id": "fa.family_id",
            "summary_data": "sa.summary_data",
            "family_data": "fa.family_data",
        }

        columns = list(self.select_accessors.values())
        return columns

    def _build_join(self, genes=None, effect_types=None):
        join_clause = ""

        if self.do_join_affected:
            pedigree_table = self.dialect.build_table_name(self.pedigree_table,
                                                           self.db)
            join_clause = f"JOIN {pedigree_table} as pedigree\n"

        if genes is not None or effect_types is not None:
            effect_gene_abs = self.where_accessors["effect_gene"]
            inner_clause = (
                f"UNNEST({effect_gene_abs})"
                if self.dialect.add_unnest_in_join()
                else effect_gene_abs
            )
            join_clause = join_clause + f"JOIN {inner_clause} \n"

        self._add_to_product(join_clause)

    def _build_from(self):
        # implicit join on family_allele and summary variants table
        from_clause = f"""\n FROM
        {self.dialect.build_table_name(self.summary_allele_table, self.db)} AS sa
        JOIN 
        {self.dialect.build_table_name(self.family_variant_table, self.db)} AS fa
        ON (fa.summary_index = sa.summary_index AND
        fa.bucket_index = sa.bucket_index AND
        fa.allele_index = sa.allele_index)""".rstrip()

        self._add_to_product(from_clause)

    def _build_group_by(self):
        pass

    def _build_having(self, **kwargs):
        pass

    def _build_where(
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
        **kwargs,
    ):
        #pylint: disable=too-many-arguments,too-many-locals
        if self.summary_allele_table:
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

        if self.summary_allele_table is not None:
            return

        if where_clause:
            in_members = "AND fa.allele_in_members = pedigree.person_id"
        else:
            in_members = "WHERE fa.allele_in_members = pedigree.person_id"
        self._add_to_product(in_members)
