class ImpalaQueryDirector:
    """Build a query in the right order."""

    def __init__(self, query_builder):
        self.query_builder = query_builder

    def build_query(
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
            limit=None,
            pedigree_fields=None):
        # pylint: disable=too-many-arguments
        """Build a query in the right order."""
        self.query_builder.reset_product()

        self.query_builder.build_select()

        self.query_builder.build_from()

        self.query_builder.build_join()

        self.query_builder.build_where(
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
            pedigree_fields=pedigree_fields,
        )

        self.query_builder.build_group_by()
        self.query_builder.build_limit(limit)
