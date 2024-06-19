from __future__ import annotations

import abc
import json
import logging
from typing import Any, Optional, cast

from dae.annotation.annotation_pipeline import AttributeInfo
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


class ZstdIndexedVariantsDataSerializer(VariantsDataSerializer):
    """Serialize family and summary alleles to zstd."""

    def __init__(self, metadata: Optional[dict[str, Any]] = None) -> None:
        super().__init__(metadata)
        if self.metadata is None:
            raise ValueError(
                "Missing metadata for ZstdIndexedVariantsDataSerializer")

        if self.metadata["version"] != "compression2.4":
            raise ValueError(
                "Bad schema version for ZstdIndexedVariantsDataSerializer")

        self.summary_f = {
            name: index
            for index, name in enumerate(self.metadata["summary_schema"])
        }
        self.summary_b = {
            index: name
            for name, index in self.summary_f.items()
        }

    def serialize_family(
        self, variant: FamilyVariant,
    ) -> bytes:
        return b""

    def serialize_summary(
        self, variant: SummaryVariant,
    ) -> bytes:
        return b""

    def deserialize_family_record(
        self, data: bytes,
    ) -> dict[str, Any]:
        return cast(dict[str, Any], data)

    def deserialize_summary_record(
        self, data: bytes,
    ) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], data)

    @classmethod
    def build_serialization_schema(
        cls, annotation_schema: list[AttributeInfo]
    ) -> dict[str, Any]:
        """Build the serialization schema."""
        fields = [
            "bucket_index",
            "summary_index",
            "allele_index",
            "sj_index",
            "chromosome",
            "position",
            "end_position",
            "variant_type",
            "transmission_type",
            "reference",
            "alternative",
            "cshl_position",
            "cshl_variant",
            "effects",
            "af_allele_count",
            "af_allele_freq",
            "af_parents_called_count",
            "af_parents_called_percent",
            "seen_as_denovo",
            "seen_in_status",
            "family_variants_count",
            "family_alleles_count",
        ]
        fields.extend([
            attr.name
            for attr in annotation_schema
            if not attr.internal
        ])

        return {
            "version": "compression2.4",
            "summary_schema": fields,
        }
