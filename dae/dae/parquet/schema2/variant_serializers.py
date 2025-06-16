from __future__ import annotations

import abc
import io
import json
import logging
from typing import Any, cast

import avro.io
import avro.schema

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
        return VariantsDataAvroSerializer(metadata)


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


PA2AVRO_SCHEMA = {
    "int8": "int",
    "int32": "int",
    "int64": "long",
    "float": "float",
    "string": "string",
    "bool": "boolean",
    "null": "null",
}


def construct_avro_summary_schema(
    schema: dict[str, str],
) -> dict[str, Any]:
    """Construct an Avro schema from the summary schema."""

    summary_schema = {
        key: value
        for key, value in schema.items()
        if key not in {
            "effect_gene", "summary_variant_data", "chromosome",
            "effect_details", "gene_effects", "region_bin",
            "frequency_bin", "coding_bin",
        }
    }

    summary_schema["effects"] = "string"
    summary_schema["chrom"] = "string"
    summary_schema["alternative"] = "string"
    summary_schema["allele_count"] = "int32"
    summary_schema["af_ref_allele_count"] = "int32"
    summary_schema["af_ref_allele_freq"] = "float"
    summary_schema["hw"] = "string"
    summary_schema["cshl_position"] = "int32"
    summary_schema["cshl_variant"] = "string"

    return {
        "type": "record",
        "name": "SummaryVariant",
        "fields": [
            {
                "name": "alleles",
                "type": {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "Allele",
                        "fields": [
                            {
                                "name": key,
                                "type": [
                                    PA2AVRO_SCHEMA.get(value) or value,
                                    "null",
                                ],
                            }
                            for key, value in summary_schema.items()
                        ],
                    },
                },
            },
        ],
    }


def construct_avro_family_schema() -> dict[str, Any]:
    """Construct an Avro schema for family variants."""
    fields = [
        {"name": "family_id", "type": "string"},
        {"name": "summary_index", "type": ["int", "null"]},
        {"name": "family_index", "type": ["int", "null"]},
        {
            "name": "genotype",
            "type": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": "int",
                },
            },
        },
        {
            "name": "best_state",
            "type": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": "int",
                },
            },
        },
        {
            "name": "inheritance_in_members",
            "type": {
                "type": "map",
                "values": {
                    "type": "array",
                    "items": {"type": "int"},
                },
            },
        },
        {
            "name": "family_variant_attributes",
            "type": {
                "type": "array",
                "items": {
                    "type": "map",
                    "values": [
                        "null",
                        "int",
                        "long",
                        "float",
                        "string",
                        "boolean",
                    ],
                },
            },
        },
    ]
    return {
        "type": "record",
        "name": "FamilyVariant",
        "fields": fields,
    }


class VariantsDataAvroSerializer(VariantsDataSerializer):
    """Interface for serializing family and summary alleles."""

    def __init__(
        self,
        summary_blob_schema: dict[str, str],
    ) -> None:
        super().__init__(summary_blob_schema)

        self.summary_blob_schema = construct_avro_summary_schema(
                summary_blob_schema)
        self.summary_avro_schema = avro.schema.parse(
            json.dumps(self.summary_blob_schema),
        )
        self.summary_avro_writer = avro.io.DatumWriter(
            self.summary_avro_schema)
        self.summary_bytes_writer = io.BytesIO()
        self.summary_encoder = avro.io.BinaryEncoder(
            self.summary_bytes_writer)

        self.family_avro_schema = avro.schema.parse(
            json.dumps(construct_avro_family_schema()),
        )
        self.family_avro_writer = avro.io.DatumWriter(
            self.family_avro_schema)
        self.family_bytes_writer = io.BytesIO()
        self.family_encoder = avro.io.BinaryEncoder(
            self.family_bytes_writer)

    def serialize_family(
        self, variant: FamilyVariant,
    ) -> bytes:
        record = variant.to_record()

        self.family_bytes_writer.seek(0)
        self.family_avro_writer.write(
            record, self.family_encoder,
        )
        return self.family_bytes_writer.getvalue()

    def deserialize_family_record(
        self, data: bytes,
    ) -> dict[str, Any]:
        bytes_reader = io.BytesIO(data)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.family_avro_schema)
        return cast(dict, reader.read(decoder))

    def serialize_summary(
        self, variant: SummaryVariant,
    ) -> bytes:
        self.summary_bytes_writer.seek(0)
        data = variant.to_record()

        self.summary_avro_writer.write(
            {"alleles": data}, self.summary_encoder,
        )
        return self.summary_bytes_writer.getvalue()

    def deserialize_summary_record(
        self, data: bytes,
    ) -> list[dict[str, Any]]:

        bytes_reader = io.BytesIO(data)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.summary_avro_schema)
        result = cast(dict, reader.read(decoder))

        return cast(list[dict], result["alleles"])
