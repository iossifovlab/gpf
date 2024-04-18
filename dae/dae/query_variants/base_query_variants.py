import abc
import logging
from collections.abc import Generator
from typing import Any, Optional

from dae.query_variants.query_runners import QueryRunner
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

RealAttrFilterType = list[tuple[str, tuple[Optional[float], Optional[float]]]]

logger = logging.getLogger(__name__)


class QueryVariantsBase(abc.ABC):
    """Base class variants' query interface."""

    RUNNER_CLASS: type[QueryRunner]

    @abc.abstractmethod
    def build_summary_variants_query_runner(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> QueryRunner:
        """Create query runner for searching summary variants."""

    @abc.abstractmethod
    def query_summary_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:
        """Execute the summary variants query and yields summary variants."""

    @abc.abstractmethod
    def build_family_variants_query_runner(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        inheritance: Optional[list[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        pedigree_fields: Optional[tuple] = None,
        **kwargs: Any,
    ) -> QueryRunner:
        # pylint: disable=too-many-arguments
        """Create a query runner for searching family variants."""

    @abc.abstractmethod
    def query_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        inheritance: Optional[list[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        pedigree_fields: Optional[tuple] = None,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        # pylint: disable=too-many-arguments
        """Execute the family variants query and yields family variants."""
