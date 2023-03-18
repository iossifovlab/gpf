import logging
from dae.query_variants.sql.schema2.base_query_builder import \
    BaseQueryBuilder, Dialect

logger = logging.getLogger(__name__)


class SummaryQueryBuilder(BaseQueryBuilder):
    """Build queries related to summary variants."""

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
        gene_models=None,
    ):
        # pylint: disable=too-many-arguments
        # self.family_variant_table = family_variant_table
        # self.summary_allele_table = summary_allele_table

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
            pedigree_df,
            gene_models=gene_models,
        )

    def _query_columns(self):
        return [
            "sa.bucket_index",
            "sa.summary_index",
            "sa.summary_variant_data",
        ]

    def _build_from(self):
        from_clause = f"""\n FROM
        {self.dialect.build_table_name(self.summary_allele_table, self.db)}
        AS sa
        """
        self._add_to_product(from_clause)

    def _build_join(self, genes=None, effect_types=None):
        if genes is not None or effect_types is not None:
            self._add_to_product("\n JOIN sa.effect_gene as eg ")

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
        **_kwargs,
    ):
        # pylint: disable=too-many-arguments,too-many-locals
        if self.summary_allele_table:
            inheritance = None
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
