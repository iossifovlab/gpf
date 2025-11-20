# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Expanded tests for ChromMappingAnnotator."""

from pathlib import Path
from typing import cast

import pytest
from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Position,
    Region,
    VCFAllele,
)
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.chrom_mapping_annotator import (
    ChromMappingAnnotator,
    build_chrom_mapping_annotator,
)

# Test __init__ method


def test_init_with_add_prefix(tmp_path: Path) -> None:
    """Test initialization with add_prefix parameter."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )
    assert annotator is not None
    assert annotator.chrom_mapping is not None


def test_init_with_del_prefix(tmp_path: Path) -> None:
    """Test initialization with del_prefix parameter."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "del_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )
    assert annotator is not None
    assert annotator.chrom_mapping is not None


def test_init_with_mapping(tmp_path: Path) -> None:
    """Test initialization with explicit mapping dictionary."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "mapping": {"1": "chr1", "2": "chr2"},
                "work_dir": tmp_path,
            },
        ),
    )
    assert annotator is not None
    assert annotator.chrom_mapping is not None


def test_init_raises_with_no_valid_config(tmp_path: Path) -> None:
    """Test initialization raises ValueError with no valid config."""
    with pytest.raises(
        ValueError,
        match="Invalid chrom_mapping configuration",
    ):
        ChromMappingAnnotator(
            None,  # type: ignore
            AnnotatorInfo(
                "test",
                [],
                {
                    "work_dir": tmp_path,
                },
            ),
        )


def test_init_creates_default_attributes_when_none(tmp_path: Path) -> None:
    """Test that default attributes are created when none provided."""
    info = AnnotatorInfo(
        "test",
        [],
        {
            "add_prefix": "chr",
            "work_dir": tmp_path,
        },
    )
    assert not info.attributes

    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        info,
    )

    assert annotator is not None
    assert len(info.attributes) == 1
    attr = info.attributes[0]
    assert attr.name == "renamed_chromosome"
    assert attr.internal is True


def test_init_preserves_existing_attributes(tmp_path: Path) -> None:
    """Test that existing attributes are preserved."""
    # Use the actual supported attribute
    custom_attr = AttributeInfo(
        "renamed_chromosome",
        "renamed_chromosome",
        internal=False,
        parameters={},
    )
    info = AnnotatorInfo(
        "test",
        [custom_attr],
        {
            "add_prefix": "chr",
            "work_dir": tmp_path,
        },
    )
    assert len(info.attributes) == 1
    assert info.attributes[0].internal is False

    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        info,
    )

    assert annotator is not None
    # Should preserve existing attribute (not replace it)
    assert len(info.attributes) == 1
    assert info.attributes[0].name == "renamed_chromosome"
    # Original internal flag should be preserved
    assert info.attributes[0].internal is False


def test_init_adds_documentation(tmp_path: Path) -> None:
    """Test that documentation is added during initialization."""
    info = AnnotatorInfo(
        "test",
        [],
        {
            "add_prefix": "chr",
            "work_dir": tmp_path,
        },
    )
    original_doc = info.documentation

    ChromMappingAnnotator(
        None,  # type: ignore
        info,
    )

    assert len(info.documentation) > len(original_doc)
    assert "chromosome" in info.documentation.lower()
    assert "naming convention" in info.documentation


def test_init_asserts_filename_is_none(tmp_path: Path) -> None:
    """Test that assertion fails if filename parameter is provided."""
    with pytest.raises(AssertionError):
        ChromMappingAnnotator(
            None,  # type: ignore
            AnnotatorInfo(
                "test",
                [],
                {
                    "add_prefix": "chr",
                    "filename": "some_file.txt",
                    "work_dir": tmp_path,
                },
            ),
        )


# Test _do_annotate method with add_prefix


@pytest.mark.parametrize("annotatable_type,annotatable,expected_chrom", [
    (Position, Position("1", 100), "chr1"),
    (Region, Region("2", 100, 200), "chr2"),
    (CNVAllele, CNVAllele("X", 1, 2, Annotatable.Type.LARGE_DELETION), "chrX"),
    (VCFAllele, VCFAllele("Y", 1, "A", "T"), "chrY"),
    (Position, Position("MT", 500), "chrMT"),
])
def test_do_annotate_add_prefix(
    annotatable_type: type,
    annotatable: Annotatable,
    expected_chrom: str,
    tmp_path: Path,
) -> None:
    """Test _do_annotate adds prefix correctly for various types."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    result = annotator._do_annotate(annotatable, {})

    assert "renamed_chromosome" in result
    renamed = cast(Annotatable, result["renamed_chromosome"])
    assert isinstance(renamed, (annotatable_type, Annotatable))
    assert renamed.chrom == expected_chrom
    assert renamed.pos == annotatable.pos


# Test _do_annotate method with del_prefix


@pytest.mark.parametrize("annotatable_type,annotatable,expected_chrom", [
    (Position, Position("chr1", 100), "1"),
    (Region, Region("chr2", 100, 200), "2"),
    (CNVAllele, CNVAllele("chrX", 1, 2, Annotatable.Type.LARGE_DELETION), "X"),
    (VCFAllele, VCFAllele("chrY", 1, "A", "T"), "Y"),
    (Position, Position("chrMT", 500), "MT"),
])
def test_do_annotate_del_prefix(
    annotatable_type: type,
    annotatable: Annotatable,
    expected_chrom: str,
    tmp_path: Path,
) -> None:
    """Test _do_annotate removes prefix correctly for various types."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "del_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    result = annotator._do_annotate(annotatable, {})

    assert "renamed_chromosome" in result
    renamed = cast(Annotatable, result["renamed_chromosome"])
    assert isinstance(renamed, (annotatable_type, Annotatable))
    assert renamed.chrom == expected_chrom
    assert renamed.pos == annotatable.pos


# Test _do_annotate with explicit mapping


def test_do_annotate_with_explicit_mapping(tmp_path: Path) -> None:
    """Test _do_annotate with explicit chromosome mapping."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "mapping": {
                    "1": "chr1",
                    "2": "chr2",
                    "X": "chrX",
                },
                "work_dir": tmp_path,
            },
        ),
    )

    pos1 = Position("1", 100)
    result1 = annotator._do_annotate(pos1, {})
    assert result1["renamed_chromosome"].chrom == "chr1"

    pos2 = Position("2", 200)
    result2 = annotator._do_annotate(pos2, {})
    assert result2["renamed_chromosome"].chrom == "chr2"

    pos_x = Position("X", 300)
    result_x = annotator._do_annotate(pos_x, {})
    assert result_x["renamed_chromosome"].chrom == "chrX"


def test_do_annotate_returns_empty_when_no_mapping(tmp_path: Path) -> None:
    """Test _do_annotate returns empty dict when chrom can't be mapped."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "mapping": {"1": "chr1"},
                "work_dir": tmp_path,
            },
        ),
    )

    # Try to annotate chromosome not in mapping
    pos = Position("2", 100)
    result = annotator._do_annotate(pos, {})

    assert not result


def test_do_annotate_preserves_original_annotatable(tmp_path: Path) -> None:
    """Test that _do_annotate doesn't modify original annotatable."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    original = Position("1", 100)
    original_chrom = original.chrom
    result = annotator._do_annotate(original, {})

    # Original should be unchanged
    assert original.chrom == original_chrom
    # Result should have modified chromosome
    assert result["renamed_chromosome"].chrom == "chr1"


def test_do_annotate_preserves_all_fields_for_vcf_allele(
    tmp_path: Path,
) -> None:
    """Test that all fields are preserved for VCFAllele."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    vcf_allele = VCFAllele("1", 100, "A", "T")
    result = annotator._do_annotate(vcf_allele, {})

    renamed = result["renamed_chromosome"]
    assert renamed.chrom == "chr1"
    assert renamed.pos == 100
    assert renamed.ref == "A"
    assert renamed.alt == "T"


def test_do_annotate_preserves_all_fields_for_cnv_allele(
    tmp_path: Path,
) -> None:
    """Test that all fields are preserved for CNVAllele."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    cnv_allele = CNVAllele("1", 100, 200, Annotatable.Type.LARGE_DELETION)
    result = annotator._do_annotate(cnv_allele, {})

    renamed = result["renamed_chromosome"]
    assert renamed.chrom == "chr1"
    assert renamed.pos == 100
    assert renamed.pos_end == 200
    assert renamed.type == Annotatable.Type.LARGE_DELETION


def test_do_annotate_preserves_all_fields_for_region(
    tmp_path: Path,
) -> None:
    """Test that all fields are preserved for Region."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "del_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    region = Region("chr1", 100, 200)
    result = annotator._do_annotate(region, {})

    renamed = result["renamed_chromosome"]
    assert renamed.chrom == "1"
    assert renamed.pos == 100
    assert renamed.pos_end == 200


# Test annotate method (public interface)


def test_annotate_public_method(tmp_path: Path) -> None:
    """Test public annotate method."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    pos = Position("1", 100)
    result = annotator.annotate(pos, {})

    assert "renamed_chromosome" in result
    assert result["renamed_chromosome"].chrom == "chr1"


# Test build_chrom_mapping_annotator factory function


def test_build_chrom_mapping_annotator(tmp_path: Path) -> None:
    """Test factory function creates annotator correctly."""
    info = AnnotatorInfo(
        "test",
        [],
        {
            "add_prefix": "chr",
            "work_dir": tmp_path,
        },
    )

    annotator = build_chrom_mapping_annotator(
        None,  # type: ignore
        info,
    )

    assert annotator is not None
    assert isinstance(annotator, ChromMappingAnnotator)
    assert annotator.chrom_mapping is not None


# Test pipeline integration


def test_pipeline_initialization_with_add_prefix(tmp_path: Path) -> None:
    """Test pipeline initialization with add_prefix."""
    pipeline_config = """
        - chrom_mapping:
            add_prefix: chr
    """

    pipeline = load_pipeline_from_yaml(
        pipeline_config,
        None,  # type: ignore
        work_dir=tmp_path,
    )

    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert isinstance(annotator, ChromMappingAnnotator)
    assert annotator.chrom_mapping is not None


def test_pipeline_initialization_with_del_prefix(tmp_path: Path) -> None:
    """Test pipeline initialization with del_prefix."""
    pipeline_config = """
        - chrom_mapping:
            del_prefix: chr
    """

    pipeline = load_pipeline_from_yaml(
        pipeline_config,
        None,  # type: ignore
        work_dir=tmp_path,
    )

    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert isinstance(annotator, ChromMappingAnnotator)


def test_pipeline_initialization_with_mapping(tmp_path: Path) -> None:
    """Test pipeline initialization with explicit mapping."""
    pipeline_config = """
        - chrom_mapping:
            mapping:
              "1": "chr1"
              "2": "chr2"
    """

    pipeline = load_pipeline_from_yaml(
        pipeline_config,
        None,  # type: ignore
        work_dir=tmp_path,
    )

    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert isinstance(annotator, ChromMappingAnnotator)


def test_pipeline_end_to_end_annotation(tmp_path: Path) -> None:
    """Test end-to-end annotation through pipeline."""
    pipeline_config = """
        - chrom_mapping:
            add_prefix: chr
    """

    pipeline = load_pipeline_from_yaml(
        pipeline_config,
        None,  # type: ignore
        work_dir=tmp_path,
    )

    pos = Position("1", 100)
    result = pipeline.annotate(pos)

    assert "renamed_chromosome" in result
    assert result["renamed_chromosome"].chrom == "chr1"
    assert result["renamed_chromosome"].pos == 100


# Test edge cases


def test_complex_mapping_with_multiple_chromosomes(tmp_path: Path) -> None:
    """Test complex mapping with multiple chromosome types."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "mapping": {
                    "1": "NC_000001.11",
                    "2": "NC_000002.12",
                    "X": "NC_000023.11",
                    "Y": "NC_000024.10",
                    "MT": "NC_012920.1",
                },
                "work_dir": tmp_path,
            },
        ),
    )

    test_cases = [
        ("1", "NC_000001.11"),
        ("2", "NC_000002.12"),
        ("X", "NC_000023.11"),
        ("Y", "NC_000024.10"),
        ("MT", "NC_012920.1"),
    ]

    for input_chrom, expected_chrom in test_cases:
        pos = Position(input_chrom, 100)
        result = annotator._do_annotate(pos, {})
        assert result["renamed_chromosome"].chrom == expected_chrom


def test_chaining_add_and_del_prefix_not_supported(tmp_path: Path) -> None:
    """Test that providing both add_prefix and del_prefix raises error."""
    # These options are mutually exclusive
    with pytest.raises(AssertionError):
        ChromMappingAnnotator(
            None,  # type: ignore
            AnnotatorInfo(
                "test",
                [],
                {
                    "add_prefix": "chr",
                    "del_prefix": "foo",
                    "work_dir": tmp_path,
                },
            ),
        )


def test_empty_context_parameter(tmp_path: Path) -> None:
    """Test that context parameter is properly ignored."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    pos = Position("1", 100)

    # Test with empty context
    result1 = annotator._do_annotate(pos, {})
    assert result1["renamed_chromosome"].chrom == "chr1"

    # Test with non-empty context (should be ignored)
    result2 = annotator._do_annotate(pos, {"some": "data"})
    assert result2["renamed_chromosome"].chrom == "chr1"


def test_special_chromosome_names(tmp_path: Path) -> None:
    """Test handling of special chromosome names."""
    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {
                "add_prefix": "chr",
                "work_dir": tmp_path,
            },
        ),
    )

    special_chroms = [
        ("M", "chrM"),
        ("MT", "chrMT"),
        ("Un", "chrUn"),
        ("random", "chrrandom"),
    ]

    for input_chrom, expected_chrom in special_chroms:
        pos = Position(input_chrom, 100)
        result = annotator._do_annotate(pos, {})
        assert result["renamed_chromosome"].chrom == expected_chrom


# Integration test


def test_full_workflow(tmp_path: Path) -> None:
    """Test complete workflow from creation to annotation."""
    # Create annotator
    info = AnnotatorInfo(
        "chrom_mapper",
        [],
        {
            "add_prefix": "chr",
            "work_dir": tmp_path,
        },
    )

    annotator = ChromMappingAnnotator(
        None,  # type: ignore
        info,
    )

    # Verify attributes were created
    assert len(info.attributes) == 1
    assert info.attributes[0].name == "renamed_chromosome"

    # Verify documentation was added
    assert len(info.documentation) > 0

    # Test annotation
    pos = Position("1", 12345)
    result = annotator.annotate(pos, {})

    assert "renamed_chromosome" in result
    renamed = result["renamed_chromosome"]
    assert renamed.chrom == "chr1"
    assert renamed.pos == 12345

    # Verify original is unchanged
    assert pos.chrom == "1"
