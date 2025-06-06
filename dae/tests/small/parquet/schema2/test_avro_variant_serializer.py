# pylint: disable=W0621,C0114,C0116,W0212,W0613,R0917

import io
import json
import pathlib
from typing import Any, cast

import avro.io
import avro.schema
import pytest
import pyzstd

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.parquet.schema2.serializers import AlleleParquetSerializer
from dae.parquet.schema2.variant_serializers import (
    VariantsDataAvroSerializer,
    construct_avro_summary_schema,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import (
    SummaryVariant,
    SummaryVariantFactory,
)
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture(scope="module")
def variants(
    acgt_genome_38: ReferenceGenome,
    tmp_path_factory: pytest.TempPathFactory,
) -> list[tuple[SummaryVariant, list[FamilyVariant]]]:

    root_path = tmp_path_factory.mktemp("test_avro_variant_serializer")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    p1		    dad1	mom1	1	2	    prb
    f1		    s1		    dad1	mom1	2	1	    sib
    f2		    mom2		0	    0	    2	1	    mom
    f2		    dad2		0	    0	    1	1	    dad
    f2		    p2	        dad2    mom2    1   2       prb
    """)

    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=chr1>
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 p1  s1  mom2 dad2 p2
    chr1   1   .  A   T   .    .      .    GT     1/1  1/1  1/0 1/1 1/1  1/1  1/0
    chr1   1   .  C   T   .    .      .    GT     1/1  1/1  1/0 1/1 1/1  1/1  1/0
    """)  # noqa: E501

    families = FamiliesLoader(ped_path).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_denovo_mode": "denovo",
    }
    vcf_loader = VcfLoader(
        families,
        [str(vcf_path)],
        acgt_genome_38,
        params=params,
    )
    return list(vcf_loader.full_variants_iterator())


@pytest.fixture(scope="module")
def annotation_pipeline(
    t4c8_grr: GenomicResourceRepo,
) -> AnnotationPipeline:
    """Fixture to provide an annotation pipeline for testing."""
    return AnnotationPipeline(t4c8_grr)


def test_allele_parquet_serializer(
    annotation_pipeline: AnnotationPipeline,
    variants: list[tuple[SummaryVariant, list[FamilyVariant]]],
) -> None:
    """Test the AlleleParquetSerializer."""

    schema_summary = AlleleParquetSerializer.build_summary_blob_schema(
        annotation_pipeline.get_attributes(),
    )
    avro_schema = avro.schema.parse(
        json.dumps(construct_avro_summary_schema(schema_summary)))

    writer = avro.io.DatumWriter(avro_schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    serialized_variants = []
    for sv, _family_variants in variants:
        bytes_writer.seek(0)
        data = sv.to_record()
        for allele in data:
            for key in allele:
                assert key in schema_summary, (
                    f"Key {key} not found in summary schema: {allele[key]}",
                )
        writer.write({"alleles": data}, encoder)
        raw_bytes = bytes_writer.getvalue()
        serialized_variants.append(raw_bytes)

    assert all(serialized_variants[0] != rb for rb in serialized_variants[1:])


def test_serialize_summary_variants(
    variants: list[tuple[SummaryVariant, list[FamilyVariant]]],
    annotation_pipeline: AnnotationPipeline,
    tmp_path: pathlib.Path,
) -> None:
    pass


@pytest.fixture
def avro_schema(
    summary_schema: dict[str, str],
) -> avro.schema.Schema:
    """Fixture to provide the Avro schema for summary variants."""
    return avro.schema.parse(
        json.dumps(construct_avro_summary_schema(summary_schema)),
    )


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

    bytes_reader = io.BytesIO(raw_bytes)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    reader = avro.io.DatumReader(avro_schema)
    result = reader.read(decoder)

    data1 = cast(dict[str, Any], result)["alleles"]
    sv1 = SummaryVariantFactory.summary_variant_from_records(
        cast(list[dict[str, Any]], data1))
    assert sv1 is not None
    assert sv1 == sv


def test_avro_blob_serializer(
    annotation_pipeline: AnnotationPipeline,
    variants: list[tuple[SummaryVariant, list[FamilyVariant]]],
) -> None:
    """Test the AlleleParquetSerializer."""

    schema_summary = AlleleParquetSerializer.build_summary_blob_schema(
        annotation_pipeline.get_attributes(),
    )

    serializer = VariantsDataAvroSerializer(schema_summary)

    for sv, _family_variants in variants:
        serialized = serializer.serialize_summary(sv)
        deserialized = serializer.deserialize_summary_record(serialized)

        assert len(deserialized) == 1
        deserialized_sv = SummaryVariantFactory.summary_variant_from_records(
            deserialized,
        )
        assert deserialized_sv is not None
        assert deserialized_sv == sv
