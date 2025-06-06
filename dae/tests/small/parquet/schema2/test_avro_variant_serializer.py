import io
import json

import avro.io
import avro.schema
import pytest
import pyzstd

from dae.variants.variant import SummaryVariant

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
    summary_schema: dict[str, str],
) -> avro.schema.Schema:
    """Construct an Avro schema from the summary schema."""
    avro_schema = {
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
    return avro.schema.parse(
        json.dumps(avro_schema),
    )


@pytest.fixture
def avro_schema_fixture(summary_schema: dict[str, str]) -> avro.schema.Schema:
    """Fixture to provide the Avro schema for summary variants."""
    schema = {
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
    return avro.schema.parse(
        json.dumps(schema),
    )


def test_explore_avro_schema_fixture(
    avro_schema_fixture: avro.schema.Schema,
) -> None:
    """Test the construction of an Avro schema fixture."""
    assert avro_schema_fixture is not None
    assert isinstance(avro_schema_fixture, avro.schema.Schema)


@pytest.fixture
def avro_schema(
    summary_schema: dict[str, str],
) -> avro.schema.Schema:
    """Fixture to provide the Avro schema for summary variants."""
    return construct_avro_summary_schema(summary_schema)


def test_avro_schema_construction(
    avro_schema: avro.schema.Schema,
) -> None:
    """Test the construction of an Avro schema."""

    assert avro_schema is not None


def test_summary_schema_fields(
    summary_schema: dict[str, str],
    sv: SummaryVariant,
) -> None:
    data = sv.to_record()

    for allele in data:
        for key in allele:
            assert key in summary_schema, (
                f"Key {key} not found in summary schema: {allele[key]}",
            )


def test_explore_avro_variant_serializer(
    sv: SummaryVariant,
    avro_schema: avro.schema.Schema,
) -> None:
    data = sv.to_record()
    assert data is not None

    assert len(json.dumps(data)) == 4070

    writer = avro.io.DatumWriter(avro_schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write({"alleles": data}, encoder)
    raw_bytes = bytes_writer.getvalue()
    print(raw_bytes)
    assert raw_bytes is not None

    assert len(raw_bytes) == 2024

    compressed = pyzstd.compress(raw_bytes, 10)
    assert len(compressed) == 548
