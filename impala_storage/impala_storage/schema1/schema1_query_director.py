from collections.abc import Iterable
from typing import List, Optional, Union

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
        query_builder: Union[
            FamilyVariantsQueryBuilder, SummaryVariantsQueryBuilder],
    ) -> None:
        self.query_builder = query_builder

    def build_query(
            self,
            regions: Optional[List[Region]] = None,
            genes: Optional[List[str]] = None,
            effect_types: Optional[List[str]] = None,
            family_ids: Optional[Iterable[str]] = None,
            person_ids: Optional[Iterable[str]] = None,
            inheritance: Optional[Union[List[str], str]] = None,
            roles: Optional[str] = None,
            sexes: Optional[str] = None,
            variant_type: Optional[str] = None,
            real_attr_filter: Optional[RealAttrFilterType] = None,
            ultra_rare: Optional[bool] = None,
            frequency_filter: Optional[RealAttrFilterType] = None,
            return_reference: Optional[bool] = None,
            return_unknown: Optional[bool] = None,
            limit: Optional[int] = None,
            pedigree_fields: Optional[tuple[list[str], list[str]]] = None,
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
