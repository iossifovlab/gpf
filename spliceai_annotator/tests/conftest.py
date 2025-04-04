# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pathlib
import textwrap

import pytest

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import build_filesystem_test_repository


@pytest.fixture
def spliceai_grr() -> GenomicResourceRepo:
    """Fixture for SpliceAI genomic resources repository."""
    return build_filesystem_test_repository(
        pathlib.Path(__file__).parent / "fixtures",
    )


@pytest.fixture
def spliceai_annotation_pipeline(
    spliceai_grr: GenomicResourceRepo,
) -> AnnotationPipeline:
    """Fixture for SpliceAI annotator."""

    pipeline_config = textwrap.dedent("""
    - spliceai_annotator:
        genome: hg19/genome_10
        gene_models: hg19/gene_models_small
        distance: 500
        attributes:
        - delta_score
    """)
    return load_pipeline_from_yaml(
        pipeline_config,
        spliceai_grr,
    )


@pytest.fixture
def spliceai_annotator(
    spliceai_annotation_pipeline: AnnotationPipeline,
) -> AnnotationPipeline:
    """Fixture for SpliceAI annotator."""
    return spliceai_annotation_pipeline.annotators[0]
