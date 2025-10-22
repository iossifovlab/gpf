# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Position,
    Region,
    VCFAllele,
)
from dae.annotation.annotation_config import AnnotatorInfo
from dae.annotation.chromosome_annotator import ChromosomeAnnotator


def test_chromosome_annotator_creation() -> None:
    annotator = ChromosomeAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {"chrom_mapping": {"add_prefix": "chr"}},
        ),
    )
    assert annotator is not None
    assert annotator.add_prefix == "chr"
    assert annotator.del_prefix is None
    annotator = ChromosomeAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {"chrom_mapping": {"del_prefix": "chr"}},
        ),
    )
    assert annotator is not None
    assert annotator.add_prefix is None
    assert annotator.del_prefix == "chr"


@pytest.mark.parametrize("annotatable_type,annotatable", [
    (Position, Position("1", 1)),
    (Region, Region("1", 1, 2)),
    (CNVAllele, CNVAllele("1", 1, 2, Annotatable.Type.LARGE_DELETION)),
    (VCFAllele, VCFAllele("1", 1, "A", "C")),
])
def test_chromosome_annotator_annotation_add_prefix(
    annotatable_type: type, annotatable: Annotatable,
) -> None:
    annotator = ChromosomeAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {"chrom_mapping": {"add_prefix": "chr"}},
        ),
    )
    output = annotator.annotate(annotatable, {})

    assert output is not None
    renamed = output["renamed_chromosome"]
    assert renamed is not None
    assert isinstance(renamed, annotatable_type)
    assert isinstance(renamed, Annotatable)
    assert renamed.chrom == "chr1"
    assert renamed.chrom != annotatable.chrom
    assert renamed.pos == annotatable.pos


@pytest.mark.parametrize("annotatable_type,annotatable", [
    (Position, Position("chr1", 1)),
    (Region, Region("chr1", 1, 2)),
    (CNVAllele, CNVAllele("chr1", 1, 2, Annotatable.Type.LARGE_DELETION)),
    (VCFAllele, VCFAllele("chr1", 1, "A", "C")),
])
def test_chromosome_annotator_annotation_del_prefix(
    annotatable_type: type, annotatable: Annotatable,
) -> None:
    annotator = ChromosomeAnnotator(
        None,  # type: ignore
        AnnotatorInfo(
            "test",
            [],
            {"chrom_mapping": {"del_prefix": "chr"}},
        ),
    )
    output = annotator.annotate(annotatable, {})

    assert output is not None
    renamed = output["renamed_chromosome"]
    assert renamed is not None
    assert isinstance(renamed, annotatable_type)
    assert isinstance(renamed, Annotatable)
    assert renamed.chrom == "1"
    assert renamed.chrom != annotatable.chrom
    assert renamed.pos == annotatable.pos
