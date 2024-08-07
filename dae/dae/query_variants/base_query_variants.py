import abc
import logging
from collections.abc import Generator
from typing import Any

import numpy as np

from dae.parquet.schema2.variant_serializers import VariantsDataSerializer
from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.query_runners import QueryRunner
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory

RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]

logger = logging.getLogger(__name__)


class QueryVariantsBase(abc.ABC):
    """Base class variants' query interface."""

    RUNNER_CLASS: type[QueryRunner]

    def __init__(self, families: FamiliesData) -> None:
        self.families = families
        self.serializer = VariantsDataSerializer.build_serializer()

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
    ) -> QueryRunner:
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
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,
        pedigree_fields: tuple | None = None,
        **kwargs: Any,
    ) -> QueryRunner:
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
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        pedigree_fields: tuple | None = None,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        # pylint: disable=too-many-arguments
        """Execute the family variants query and yields family variants."""

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
