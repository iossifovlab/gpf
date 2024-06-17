from __future__ import annotations

import abc
import json
import logging
from typing import Any, Optional, cast

from dae.variants.family_variant import (
    FamilyVariant,
)
from dae.variants.variant import (
    SummaryVariant,
)

logger = logging.getLogger(__name__)


class VariantsDataSerializer(abc.ABC):
    """Interface for serializing family and summary alleles."""

    def __init__(self, metadata: Optional[dict[str, Any]] = None) -> None:
        self.metadata = metadata

    @abc.abstractmethod
    def serialize_family(
        self, variant: FamilyVariant,
    ) -> bytes:
        """Serialize a family variant part to a byte string."""

    @abc.abstractmethod
    def serialize_summary(
        self, variant: SummaryVariant,
    ) -> bytes:
        """Serialize a summary allele to a byte string."""

    @abc.abstractmethod
    def deserialize_family_record(
        self, data: bytes,
    ) -> dict[str, Any]:
        """Deserialize a family allele from a byte string."""

    @abc.abstractmethod
    def deserialize_summary_record(
        self, data: bytes,
    ) -> list[dict[str, Any]]:
        """Deserialize a summary allele from a byte string."""

    @staticmethod
    def build_serializer(
        metadata: Optional[dict[str, Any]] = None,
    ) -> VariantsDataSerializer:
        """Build a serializer based on the metadata."""
        return JsonVariantsDataSerializer(metadata)


class JsonVariantsDataSerializer(VariantsDataSerializer):
    """Serialize family and summary alleles to json."""

    def serialize_family(
        self, variant: FamilyVariant,
    ) -> bytes:
        return json.dumps(variant.to_record(), sort_keys=True).encode()

    def serialize_summary(
        self, variant: SummaryVariant,
    ) -> bytes:
        return json.dumps(variant.to_record(), sort_keys=True).encode()

    def deserialize_family_record(
        self, data: bytes,
    ) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(data))

    def deserialize_summary_record(
        self, data: bytes,
    ) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], json.loads(data))
