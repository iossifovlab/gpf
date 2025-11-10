# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
from typing import cast

import pytest
from dae.annotation.score_annotator import GenomicScoreAnnotatorBase
from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.histogram import NumberHistogram
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceProtocolRepo,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_group_repository,
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    build_inmemory_test_repository,
    setup_directories,
    setup_empty_gene_models,
    setup_genome,
)
from dae.genomic_scores.scores import _build_score_help
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.setup_helpers import setup_gpf_instance


@pytest.fixture
def scores_repo() -> GenomicResourceProtocolRepo:
    return build_inmemory_test_repository({
        "phastCons": {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                  filename: phastCons100.bedGraph.gz
                  format: tabix
                  header_mode: none
                  chrom:
                    index: 0
                  pos_begin:
                    index: 1
                  pos_end:
                    index: 2
                scores:
                  - id: phastCons100
                    index: 3
                    type: float
                    desc: phastCons100 desc
                    histogram:
                      type: number
                      number_of_bins: 10
                      view_range:
                        max: 1.0
                        min: 0.0

                default_annotation:
                  - source: phastCons100
                    name: phastcons100
                meta:
                  description:
                    test_help
                  labels: ~
            """),
            "statistics": {
                "histogram_phastCons100.json": textwrap.dedent("""{
                    "bars": [
                        470164,
                        48599,
                        25789,
                        16546,
                        9269,
                        6170,
                        4756,
                        4633,
                        5240,
                        25736
                    ],
                    "bins": [
                        0.0,
                        0.1,
                        0.2,
                        0.30000000000000004,
                        0.4,
                        0.5,
                        0.6000000000000001,
                        0.7000000000000001,
                        0.8,
                        0.9,
                        1.0
                    ],
                    "config": {
                      "type": "number",
                      "number_of_bins": 10,
                      "view_range": {
                        "max": 1.0,
                        "min": 0.0
                      },
                      "x_log_scale": false,
                      "x_min_log": null,
                      "y_log_scale": false
                    }
                }
                """),
            },
        },
    })


@pytest.fixture
def annotation_gpf(
    scores_repo: GenomicResourceProtocolRepo,
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("genomic_scores_db_gpf")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        instance_id: test_instance
        annotation:
            conf_file: annotation.yaml
        """),
        "annotation.yaml": textwrap.dedent("""
        - position_score: phastCons
        """),
    })
    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")

    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })

    return setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=build_genomic_resource_group_repository(
            "aaa", [local_repo, scores_repo]),
    )


def test_genomic_scores_db_with_annotation(
    annotation_gpf: GPFInstance,
) -> None:
    assert annotation_gpf is not None
    annotaiton_pipeline = annotation_gpf.get_annotation_pipeline()
    assert annotaiton_pipeline is not None

    registry = annotation_gpf.genomic_scores
    assert registry is not None
    assert len(registry.get_scores()) == 1
    assert "phastcons100" in registry
    assert registry["phastcons100"] is not None

    score = registry["phastcons100"]
    assert score.hist is not None
    assert isinstance(score.hist, NumberHistogram)

    assert len(score.hist.bars) == 10
    assert len(score.hist.bins) == 11
    assert not score.hist.config.x_log_scale
    assert not score.hist.config.y_log_scale


def test_build_score_help(
    annotation_gpf: GPFInstance,
    scores_repo: GenomicResourceProtocolRepo,
) -> None:
    annotation_pipeline = annotation_gpf.get_annotation_pipeline()
    assert annotation_pipeline is not None
    assert len(annotation_pipeline.annotators) > 0

    # Find the position_score annotator
    score_annotator = None
    for annotator in annotation_pipeline.annotators:
        if annotator.get_info().type == "position_score":
            score_annotator = annotator
            break

    assert score_annotator is not None
    annotator_info = score_annotator.get_info()
    assert annotator_info.type == "position_score"

    # Get the first attribute
    attr_info = annotator_info.attributes[0]
    assert attr_info.name == "phastcons100"

    # Build the genomic score
    resource = scores_repo.get_resource("phastCons")
    genomic_score = build_score_from_resource(resource)

    # Build the help text
    help_text = _build_score_help(
        cast(GenomicScoreAnnotatorBase, score_annotator),
        attr_info, genomic_score)

    # Verify the help text contains expected elements
    assert help_text is not None
    assert len(help_text) > 0
    assert "phastcons100" in help_text
    assert "phastCons100 desc" in help_text
    assert "phastCons" in help_text
    assert "position_score" in help_text
    assert '<div class="score-description">' in help_text
    assert "Genomic resource:" in help_text
    assert "histogram" in help_text.lower()
    assert "details" in help_text.lower()
    assert "**source**:" in help_text
    assert "**resource_type**:" in help_text
    assert "**annotator_type**:" in help_text
