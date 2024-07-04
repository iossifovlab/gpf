from __future__ import annotations

import abc
import json
import logging
from typing import Any, cast

import pyzstd

from dae.variants.family_variant import (
    FamilyVariant,
)
from dae.variants.variant import (
    SummaryVariant,
)

logger = logging.getLogger(__name__)


class VariantsDataSerializer(abc.ABC):
    """Interface for serializing family and summary alleles."""

    def __init__(self, metadata: dict[str, Any] | None = None) -> None:
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
        metadata: dict[str, Any] | None = None,
    ) -> VariantsDataSerializer:
        """Build a serializer based on the metadata."""
        if metadata is None:
            return JsonVariantsDataSerializer(metadata)
        if metadata["version"] == "compression2.4":
            return ZstdIndexedVariantsDataSerializer(metadata)
        raise ValueError(f"Unknown metadata version: {metadata['version']}")


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

    def __init__(self, metadata: dict[str, Any] | None = None) -> None:
        super().__init__(metadata)
        if self.metadata is None:
            raise ValueError(
                "Missing metadata for ZstdIndexedVariantsDataSerializer")

        if self.metadata["version"] != "compression2.4":
            raise ValueError(
                "Bad schema version for ZstdIndexedVariantsDataSerializer")

        self.summary_f = dict(self.metadata["summary_fields"])
        self.summary_b = {
            index: name
            for name, index in self.summary_f.items()
        }

        self.family_f = dict(self.metadata["family_fields"])
        self.family_b = {
            index: name
            for name, index in self.family_f.items()
        }

    def serialize_family(
        self, variant: FamilyVariant,
    ) -> bytes:
        record = [
            [self.family_f[key], val]
            for key, val in variant.to_record().items()
        ]
        return pyzstd.compress(json.dumps(record, sort_keys=True).encode())

    def deserialize_family_record(
        self, data: bytes,
    ) -> dict[str, Any]:
        return {
            self.family_b[key]: val
            for key, val in json.loads(pyzstd.decompress(data))
        }

    def serialize_summary(
        self, variant: SummaryVariant,
    ) -> bytes:
        record = [
            [
                [self.summary_f[key], val]
                for key, val in rec.items()
            ]
            for rec in variant.to_record()
        ]
        return pyzstd.compress(json.dumps(record, sort_keys=True).encode())

    def deserialize_summary_record(
        self, data: bytes,
    ) -> list[dict[str, Any]]:
        record = json.loads(pyzstd.decompress(data))
        return [
            {
                self.summary_b[key]: val
                for key, val in rec
            }
            for rec in record
        ]

    @classmethod
    def build_serialization_meta(
        cls, annotation_fields: list[str],
    ) -> dict[str, Any]:
        """Build the serialization schema."""
        summary_fields = [
            ["bucket_index", 0],
            ["summary_index", 1],
            ["allele_index", 2],
            ["allele_count", 3],
            ["sj_index", 4],
            ["chrom", 5],
            ["position", 6],
            ["end_position", 7],
            ["variant_type", 8],
            ["transmission_type", 9],
            ["reference", 10],
            ["alternative", 11],
            ["cshl_position", 12],
            ["cshl_variant", 13],
            ["effects", 14],
            ["af_allele_count", 15],
            ["af_allele_freq", 16],
            ["af_ref_allele_count", 160],
            ["af_ref_allele_freq", 161],
            ["af_parents_called_count", 17],
            ["af_parents_called_percent", 18],
            ["hw", 19],
            ["seen_as_denovo", 20],
            ["seen_in_status", 21],
            ["family_variants_count", 22],
            ["family_alleles_count", 23],
        ]
        summary_fields.extend([
            [name, index]
            for index, name in enumerate(annotation_fields, 1000)
        ])

        seen = set()
        for name, _index in summary_fields:
            if name in seen:
                raise ValueError(f"duplicate field name: {name}")
            seen.add(name)

        family_fields = [
            ["summary_index", 0],
            ["family_index", 1],
            ["family_id", 2],
            ["genotype", 3],
            ["best_state", 4],
            ["inheritance_in_members", 5],
        ]
        return {
            "version": "compression2.4",
            "summary_fields": summary_fields,
            "family_fields": family_fields,
        }
