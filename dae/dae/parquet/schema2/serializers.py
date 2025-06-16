from __future__ import annotations

import abc
import functools
import io
import json
import logging
import operator
from itertools import starmap
from typing import Any, ClassVar, cast

import avro.io
import avro.schema
import pyarrow as pa

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.variants.attributes import (
    Inheritance,
    Role,
    Sex,
    Status,
    TransmissionType,
)
from dae.variants.core import Allele
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant

logger = logging.getLogger(__name__)


class AlleleParquetSerializer:
    """Serialize a bunch of alleles."""

    SUMMARY_ALLELE_BASE_SCHEMA: ClassVar[dict[str, Any]] = {
        "bucket_index": pa.int32(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "sj_index": pa.int64(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        "effect_gene": pa.list_(
            pa.struct([
                pa.field("effect_gene_symbols", pa.string()),
                pa.field("effect_types", pa.string()),
            ]),
        ),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string(),
        "af_allele_count": pa.int32(),
        "af_allele_freq": pa.float32(),
        "af_parents_called_count": pa.int32(),
        "af_parents_called_percent": pa.float32(),
        "seen_as_denovo": pa.bool_(),
        "seen_in_status": pa.int8(),
        "family_variants_count": pa.int32(),
        "family_alleles_count": pa.int32(),
    }

    FAMILY_ALLELE_BASE_SCHEMA: ClassVar[dict[str, Any]] = {
        "bucket_index": pa.int32(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "sj_index": pa.int64(),
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "allele_in_sexes": pa.int8(),
        "allele_in_statuses": pa.int8(),
        "allele_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "zygosity_in_status": pa.int8(),
        "zygosity_in_roles": pa.int64(),
        "zygosity_in_sexes": pa.int16(),
        "allele_in_members": pa.list_(pa.string()),
    }

    ENUM_PROPERTIES: ClassVar[dict[str, Any]] = {
        "variant_type": Allele.Type,
        "transmission_type": TransmissionType,
        "allele_in_sexes": Sex,
        "allele_in_roles": Role,
        "allele_in_statuses": Status,
        "inheritance_in_members": Inheritance,
    }

    def __init__(
        self, annotation_schema: list[AttributeInfo],
        extra_attributes: list[str] | None = None,
    ) -> None:
        self.annotation_schema = annotation_schema
        self._schema_summary: pa.Schema | None = None
        self._schema_family: pa.Schema | None = None

        self.extra_attributes = []
        if extra_attributes:
            for attribute_name in extra_attributes:
                self.extra_attributes.append(attribute_name)

    @property
    def schema_summary(self) -> pa.Schema:
        """Lazy construct and return the schema for the summary alleles."""
        if self._schema_summary is None:
            self._schema_summary = self.build_summary_schema(
                self.annotation_schema,
            )
        return self._schema_summary

    @classmethod
    def build_summary_schema(
        cls, annotation_schema: list[AttributeInfo],
    ) -> pa.Schema:
        """Build the schema for the summary alleles."""
        fields = list(
            starmap(pa.field, cls.SUMMARY_ALLELE_BASE_SCHEMA.items()))
        fields.append(pa.field("summary_variant_data", pa.binary()))

        annotation_type_to_pa_type = {
            "float": pa.float32(),
            "int": pa.int32(),
            "str": pa.string(),
        }

        if annotation_schema is not None:
            for attr in annotation_schema:
                if attr.internal:
                    continue
                if attr.type in annotation_type_to_pa_type:
                    fields.append(
                        pa.field(
                            attr.name,
                            annotation_type_to_pa_type[attr.type],
                        ),
                    )
        return pa.schema(fields)

    @classmethod
    def build_summary_blob_schema(
        cls, annotation_schema: list[AttributeInfo],
    ) -> dict[str, str]:

        schema_summary = cls.build_summary_schema(annotation_schema)
        return {
            f.name: str(f.type)
            for f in schema_summary
            if f.name not in {
                "effect_gene", "summary_variant_data", "chromosome",
            }
        }

    @property
    def schema_family(self) -> pa.Schema:
        """Lazy construct and return the schema for the family alleles."""
        if self._schema_family is None:
            self._schema_family = self.build_family_schema()
        return self._schema_family

    @classmethod
    def build_family_schema(cls) -> pa.Schema:
        """Build the schema for the family alleles."""
        fields = list(starmap(pa.field, cls.FAMILY_ALLELE_BASE_SCHEMA.items()))
        fields.append(pa.field("family_variant_data", pa.binary()))
        return pa.schema(fields)

    def _get_searchable_prop_value(
        self, allele: SummaryAllele | FamilyAllele,
        spr: str,
    ) -> Any:
        prop_value = getattr(allele, spr, None)

        if prop_value is None:
            prop_value = allele.get_attribute(spr)
        if prop_value and spr in self.ENUM_PROPERTIES:
            if isinstance(prop_value, list):
                prop_value = functools.reduce(
                    operator.or_,
                    [enum.value for enum in prop_value if enum is not None],
                    0,
                )
            else:
                prop_value = prop_value.value
        return prop_value

    def build_family_allele_batch_dict(
        self, allele: FamilyAllele,
        family_variant_data: bytes,
    ) -> dict[str, list[Any]]:
        """Build a batch of family allele data in the form of a dict."""
        family_header = []
        family_properties = []

        for spr in self.FAMILY_ALLELE_BASE_SCHEMA:
            prop_value = self._get_searchable_prop_value(allele, spr)

            family_header.append(spr)
            family_properties.append(prop_value)

        assert family_header[-1] == "allele_in_members"
        family_properties[-1] = [v for v in family_properties[-1] if v]

        allele_data: dict[str, list] = {
            name: [] for name in self.schema_family.names
        }
        for name, value in zip(
                family_header,
                family_properties,
                strict=True):
            allele_data[name].append(value)

        allele_data["family_variant_data"] = [family_variant_data]
        return allele_data

    def build_summary_allele_batch_dict(
        self, allele: SummaryAllele,
        summary_variant_data: bytes,
    ) -> dict[str, Any]:
        """Build a batch of summary allele data in the form of a dict."""
        allele_data = {"summary_variant_data": summary_variant_data}

        for spr in self.SUMMARY_ALLELE_BASE_SCHEMA:

            if spr == "effect_gene":
                if allele.effect_types is None:
                    assert allele.effect_gene_symbols is None
                    prop_value = [
                        {"effect_types": None, "effect_gene_symbols": None},
                    ]
                else:
                    prop_value = [
                        {"effect_types": e[0], "effect_gene_symbols": e[1]}
                        for e in zip(
                            allele.effect_types,
                            allele.effect_gene_symbols,
                            strict=True,
                        )
                    ]
            else:
                prop_value = self._get_searchable_prop_value(allele, spr)

            allele_data[spr] = prop_value  # type: ignore

        if self.annotation_schema is not None:
            for attr in self.annotation_schema:
                if attr.internal:
                    continue
                allele_data[attr.name] = allele.get_attribute(attr.name)

        return allele_data


class VariantsDataSerializer(abc.ABC):
    """Interface for serializing family and summary alleles."""

    def __init__(self, metadata: dict[str, Any]) -> None:
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
        metadata: dict[str, Any],
        serializer_type: str = "json",
    ) -> VariantsDataSerializer:
        """Build a serializer based on the metadata."""
        if serializer_type == "json":
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
