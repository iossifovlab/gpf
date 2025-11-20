# pylint: disable=W0621,C0114,C0116,W0212,W0613

from pathlib import Path

import pytest
from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Position,
    Region,
    VCFAllele,
)
from dae.annotation.annotation_config import AnnotatorInfo
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.chrom_mapping_annotator import ChromMappingAnnotator


def test_chromosome_annotator_creation(tmp_path: Path) -> None:
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


@pytest.mark.parametrize("annotatable_type,annotatable", [
    (Position, Position("1", 1)),
    (Region, Region("1", 1, 2)),
    (CNVAllele, CNVAllele("1", 1, 2, Annotatable.Type.LARGE_DELETION)),
    (VCFAllele, VCFAllele("1", 1, "A", "C")),
])
def test_chromosome_annotator_annotation_add_prefix(
    annotatable_type: type, annotatable: Annotatable,
    tmp_path: Path,
) -> None:
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
    tmp_path: Path,
) -> None:
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
    output = annotator.annotate(annotatable, {})

    assert output is not None
    renamed = output["renamed_chromosome"]
    assert renamed is not None
    assert isinstance(renamed, annotatable_type)
    assert isinstance(renamed, Annotatable)
    assert renamed.chrom == "1"
    assert renamed.chrom != annotatable.chrom
    assert renamed.pos == annotatable.pos


def test_pipeline_initialization(tmp_path: Path) -> None:
    pipeline_config = """
        - chrom_mapping:
            add_prefix: chr
    """

    pipeline = load_pipeline_from_yaml(
        pipeline_config, None, work_dir=tmp_path,  # type: ignore
    )
    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert annotator is not None
    assert isinstance(annotator, ChromMappingAnnotator)
    assert annotator.chrom_mapping is not None
