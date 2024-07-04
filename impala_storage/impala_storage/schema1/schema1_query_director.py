from collections.abc import Iterable
from typing import List

from dae.utils.regions import Region
from impala_storage.schema1.family_variants_query_builder import (
    FamilyVariantsQueryBuilder,
)
from impala_storage.schema1.summary_variants_query_builder import (
    RealAttrFilterType,
    SummaryVariantsQueryBuilder,
)


class ImpalaQueryDirector:
    """Build a query in the right order."""

    def __init__(
        self,
        query_builder: FamilyVariantsQueryBuilder | SummaryVariantsQueryBuilder,
    ) -> None:
        self.query_builder = query_builder

    def build_query(
            self,
            regions: List[Region] | None = None,
            genes: List[str] | None = None,
            effect_types: List[str] | None = None,
            family_ids: Iterable[str] | None = None,
            person_ids: Iterable[str] | None = None,
            inheritance: List[str] | str | None = None,
            roles: str | None = None,
            sexes: str | None = None,
            variant_type: str | None = None,
            real_attr_filter: RealAttrFilterType | None = None,
            ultra_rare: bool | None = None,
            frequency_filter: RealAttrFilterType | None = None,
            return_reference: bool | None = None,
            return_unknown: bool | None = None,
            limit: int | None = None,
            pedigree_fields: tuple[list[str], list[str]] | None = None,
    ) -> None:
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
