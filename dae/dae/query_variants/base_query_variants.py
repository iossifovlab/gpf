import abc
import logging
from collections.abc import Generator
from typing import Any

import numpy as np

from dae.parquet.schema2.variant_serializers import VariantsDataSerializer
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import FamilyTag
from dae.pedigrees.family_tag_builder import check_family_tags_query
from dae.query_variants.query_runners import QueryRunner
from dae.query_variants.sql.schema2.sql_query_builder import (
    TagsQuery,
    ZygosityQuery,
)
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory

RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]

logger = logging.getLogger(__name__)


class QueryVariants(abc.ABC):
    """Abstract class for querying variants interface."""

    @abc.abstractmethod
    def has_affected_status_queries(self) -> bool:
        """Return True if the storage supports affected status queries."""

    @abc.abstractmethod
    def build_summary_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> QueryRunner | None:
        """Create query runner for searching summary variants."""

    @abc.abstractmethod
    def query_summary_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:
        """Execute the summary variants query and yields summary variants."""

    @abc.abstractmethod
    def build_family_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles_in_parent: str | None = None,
        roles_in_child: str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,
        tags_query: TagsQuery | None = None,
        zygosity_query: ZygosityQuery | None = None,
        **kwargs: Any,
    ) -> QueryRunner | None:
        # pylint: disable=too-many-arguments
        """Create a query runner for searching family variants."""

    @abc.abstractmethod
    def query_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles_in_parent: str | None = None,
        roles_in_child: str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        tags_query: TagsQuery | None = None,
        zygosity_query: ZygosityQuery | None = None,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        # pylint: disable=too-many-arguments
        """Execute the family variants query and yields family variants."""


class QueryVariantsBase(QueryVariants):
    """Base class variants for Schema2 query interface."""

    RUNNER_CLASS: type[QueryRunner]

    def __init__(self, families: FamiliesData) -> None:
        self.families = families
        self.serializer = VariantsDataSerializer.build_serializer()

    @staticmethod
    def transform_roles_to_single_role_string(
        roles_in_parent: str | None, roles_in_child: str | None,
        roles: str | None = None,
    ) -> str | None:
        """
        Transform roles arguments into singular roles argument.

        Helper method for supporting legacy backends.
        """
        if roles_in_child is None and roles_in_parent is None:
            return roles
        if roles_in_parent and roles_in_child:
            return f"({roles_in_parent}) and ({roles_in_child})"
        return roles_in_child or roles_in_parent

    def has_affected_status_queries(self) -> bool:
        """Schema2 do support affected status queries."""
        return True

    def deserialize_summary_variant(
        self, sv_data: bytes,
    ) -> SummaryVariant:
        """Deserialize a summary variant from a summary blob."""
        sv_record = self.serializer.deserialize_summary_record(sv_data)
        return SummaryVariantFactory.summary_variant_from_records(
            sv_record,
        )

    def deserialize_family_variant(
        self, sv_data: bytes, fv_data: bytes,
    ) -> FamilyVariant:
        """Deserialize a family variant from a summary and family blobs."""
        sv_record = self.serializer.deserialize_summary_record(sv_data)
        fv_record = self.serializer.deserialize_family_record(fv_data)
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        fattributes = fv_record.get("family_variant_attributes")
        fv = FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record,
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members,
        )
        if fattributes:
            for fa, fattr in zip(
                    fv.family_alt_alleles, fattributes, strict=True):
                fa.update_attributes(fattr)
        return fv

    def tags_to_family_ids(
        self, tags_query: TagsQuery | None = None,
    ) -> set[str] | None:
        """Transform a query for tags into a set of family IDs."""
        if tags_query is None:
            return None

        if tags_query.selected_family_tags is None \
                and tags_query.deselected_family_tags is None:
            return None

        if isinstance(tags_query.selected_family_tags, list):
            include_tags = {
                FamilyTag.from_label(label)
                for label
                in tags_query.selected_family_tags
            }
        else:
            include_tags = set[FamilyTag]()
        if isinstance(tags_query.deselected_family_tags, list):
            exclude_tags = {
                FamilyTag.from_label(label)
                for label
                in tags_query.deselected_family_tags
            }
        else:
            exclude_tags = set[FamilyTag]()

        family_ids: set[str] = set()
        for family_id, family in self.families.items():
            if check_family_tags_query(
                family,
                or_mode=tags_query.tags_or_mode,
                include_tags=include_tags,
                exclude_tags=exclude_tags,
            ):
                family_ids.add(family_id)

        return family_ids
