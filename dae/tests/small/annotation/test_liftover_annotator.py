# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
from dae.annotation.annotation_config import AnnotatorInfo
from dae.annotation.annotation_factory import (
    load_pipeline_from_yaml,
)
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.liftover_annotator import (
    BasicLiftoverAnnotator,
    BcfLiftoverAnnotator,
    build_liftover_annotator,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_gzip,
)


@pytest.fixture
def dummy_liftover_grr_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("dummy_liftover_grr_fixture")
    setup_directories(root_path, {
        "genomeA": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "genomeB": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "dummyChain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain
                filename: liftover.chain.gz
                meta:
                  labels:
                    source_genome: genomeA
                    target_genome: genomeB
            """),
        },
    })
    setup_gzip(
        root_path / "dummyChain" / "liftover.chain.gz",
        convert_to_tab_separated("""
        chain 2200 22 40 + 20 40 chr22 20 + 0 20 4a
        20 0 0
        0

        """),
    )

    return build_filesystem_test_repository(root_path)


def test_liftover_annotator_implicit_genomes(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: dummyChain
      """)
    pipeline = load_pipeline_from_yaml(
        pipeline_config, dummy_liftover_grr_fixture)
    assert pipeline.get_resource_ids() == {
        "genomeA",
        "genomeB",
        "dummyChain",
    }


def test_build_liftover_annotator_bcf_type(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test build_liftover_annotator creates BcfLiftoverAnnotator."""
    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: dummyChain
      """)
    pipeline = load_pipeline_from_yaml(
        pipeline_config, dummy_liftover_grr_fixture)

    # Get the annotator from the pipeline
    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert isinstance(annotator, BcfLiftoverAnnotator)


def test_build_liftover_annotator_basic_type(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test build_liftover_annotator creates BasicLiftoverAnnotator."""
    pipeline_config = textwrap.dedent("""
      - basic_liftover_annotator:
          chain: dummyChain
      """)
    pipeline = load_pipeline_from_yaml(
        pipeline_config, dummy_liftover_grr_fixture)

    # Get the annotator from the pipeline
    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert isinstance(annotator, BasicLiftoverAnnotator)


def test_build_liftover_annotator_explicit_genomes(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test build_liftover_annotator with explicit genomes."""
    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: dummyChain
          source_genome: genomeA
          target_genome: genomeB
      """)
    pipeline = load_pipeline_from_yaml(
        pipeline_config, dummy_liftover_grr_fixture)

    assert len(pipeline.annotators) == 1
    annotator = pipeline.annotators[0]
    assert isinstance(annotator, BcfLiftoverAnnotator)


def test_build_liftover_annotator_missing_chain(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test build_liftover_annotator raises error when chain is missing."""
    pipeline = AnnotationPipeline(dummy_liftover_grr_fixture)
    info = AnnotatorInfo(
        "liftover_annotator",
        [],
        {},  # No chain parameter
    )

    with pytest.raises(ValueError, match="requires a 'chain' parameter"):
        build_liftover_annotator(pipeline, info)


def test_build_liftover_annotator_invalid_chain_resource(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test error when chain resource is unavailable."""
    pipeline = AnnotationPipeline(dummy_liftover_grr_fixture)
    info = AnnotatorInfo(
        "liftover_annotator",
        [],
        {"chain": "nonexistent_chain"},
    )

    with pytest.raises(FileNotFoundError, match=r"resource .* not found"):
        build_liftover_annotator(pipeline, info)


def test_build_liftover_annotator_invalid_target_genome(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test error when target genome is unavailable."""
    pipeline = AnnotationPipeline(dummy_liftover_grr_fixture)
    info = AnnotatorInfo(
        "liftover_annotator",
        [],
        {"chain": "dummyChain", "target_genome": "nonexistent_genome"},
    )

    with pytest.raises(FileNotFoundError, match=r"resource .* not found"):
        build_liftover_annotator(pipeline, info)


def test_build_liftover_annotator_invalid_source_genome(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test error when source genome is unavailable."""
    pipeline = AnnotationPipeline(dummy_liftover_grr_fixture)
    info = AnnotatorInfo(
        "liftover_annotator",
        [],
        {"chain": "dummyChain", "source_genome": "nonexistent_genome"},
    )

    with pytest.raises(FileNotFoundError, match=r"resource .* not found"):
        build_liftover_annotator(pipeline, info)


def test_build_liftover_annotator_unsupported_type(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    """Test error for unsupported annotator type."""
    pipeline = AnnotationPipeline(dummy_liftover_grr_fixture)
    info = AnnotatorInfo(
        "unsupported_liftover_annotator",
        [],
        {"chain": "dummyChain"},
    )

    with pytest.raises(ValueError, match="Unsupported liftover annotator type"):
        build_liftover_annotator(pipeline, info)
