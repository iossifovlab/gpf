# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
from typing import cast

import pytest
from dae.annotation.score_annotator import GenomicScoreAnnotatorBase
from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    NullHistogram,
    NumberHistogram,
)
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
from dae.genomic_scores.scores import (
    GenomicScoresRegistry,
    ScoreDesc,
    _build_score_help,
)
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


def test_score_desc_to_json(annotation_gpf: GPFInstance) -> None:
    """Test ScoreDesc serialization to JSON."""
    registry = annotation_gpf.genomic_scores
    assert registry is not None

    score = registry["phastcons100"]
    json_data = score.to_json()

    assert json_data is not None
    assert json_data["name"] == "phastcons100"
    assert json_data["resource_id"] == "phastCons"
    assert json_data["source"] == "phastCons100"
    assert "hist" in json_data
    assert json_data["description"] is not None
    assert json_data["help"] is not None
    assert "small_values_desc" in json_data
    assert "large_values_desc" in json_data


def test_score_desc_from_json(annotation_gpf: GPFInstance) -> None:
    """Test ScoreDesc deserialization from JSON."""
    registry = annotation_gpf.genomic_scores
    assert registry is not None

    original_score = registry["phastcons100"]
    json_data = original_score.to_json()

    # Deserialize from JSON
    restored_score = ScoreDesc.from_json(json_data)

    assert restored_score.name == original_score.name
    assert restored_score.resource_id == original_score.resource_id
    assert restored_score.source == original_score.source
    assert restored_score.description == original_score.description
    assert restored_score.help == original_score.help
    assert isinstance(restored_score.hist, NumberHistogram)


def test_score_desc_from_json_number_histogram() -> None:
    """Test ScoreDesc.from_json with number histogram."""
    json_data = {
        "name": "test_score",
        "resource_id": "test_resource",
        "source": "test_source",
        "description": "Test description",
        "help": "Test help",
        "small_values_desc": "Small values",
        "large_values_desc": "Large values",
        "hist": {
            "config": {
                "type": "number",
                "number_of_bins": 5,
                "view_range": {"min": 0.0, "max": 1.0},
                "x_log_scale": False,
                "y_log_scale": False,
            },
            "bars": [10, 20, 30, 20, 10],
            "bins": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        },
    }

    score = ScoreDesc.from_json(json_data)
    assert score.name == "test_score"
    assert isinstance(score.hist, NumberHistogram)
    assert len(score.hist.bars) == 5


def test_score_desc_from_json_categorical_histogram() -> None:
    """Test ScoreDesc.from_json with categorical histogram."""
    json_data = {
        "name": "test_score",
        "resource_id": "test_resource",
        "source": "test_source",
        "description": "Test description",
        "help": "Test help",
        "small_values_desc": None,
        "large_values_desc": None,
        "hist": {
            "config": {
                "type": "categorical",
                "y_log_scale": False,
            },
            "bars": [100, 200, 50],
            "values": ["A", "B", "C"],
        },
    }

    score = ScoreDesc.from_json(json_data)
    assert score.name == "test_score"
    assert isinstance(score.hist, CategoricalHistogram)


def test_score_desc_from_json_null_histogram() -> None:
    """Test ScoreDesc.from_json with null histogram."""
    json_data = {
        "name": "test_score",
        "resource_id": "test_resource",
        "source": "test_source",
        "description": "Test description",
        "help": "Test help",
        "small_values_desc": None,
        "large_values_desc": None,
        "hist": {
            "config": {
                "type": "null",
                "reason": "No data available",
            },
        },
    }

    score = ScoreDesc.from_json(json_data)
    assert score.name == "test_score"
    assert isinstance(score.hist, NullHistogram)


def test_score_desc_from_json_unknown_histogram_type() -> None:
    """Test ScoreDesc.from_json with unknown histogram type raises error."""
    json_data = {
        "name": "test_score",
        "resource_id": "test_resource",
        "source": "test_source",
        "description": "Test description",
        "help": "Test help",
        "small_values_desc": None,
        "large_values_desc": None,
        "hist": {
            "config": {
                "type": "unknown_type",
            },
        },
    }

    with pytest.raises(ValueError, match="Unknown histogram type"):
        ScoreDesc.from_json(json_data)


def test_genomic_scores_registry_get_scores(
    annotation_gpf: GPFInstance,
) -> None:
    """Test GenomicScoresRegistry.get_scores method."""
    registry = annotation_gpf.genomic_scores
    assert registry is not None

    scores = registry.get_scores()
    assert len(scores) == 1
    assert scores[0][0] == "phastcons100"
    assert isinstance(scores[0][1], ScoreDesc)


def test_genomic_scores_registry_getitem(
    annotation_gpf: GPFInstance,
) -> None:
    """Test GenomicScoresRegistry __getitem__ method."""
    registry = annotation_gpf.genomic_scores
    assert registry is not None

    score = registry["phastcons100"]
    assert score is not None
    assert score.name == "phastcons100"


def test_genomic_scores_registry_getitem_missing() -> None:
    """Test GenomicScoresRegistry __getitem__ with missing score."""
    registry = GenomicScoresRegistry({})

    with pytest.raises(KeyError):
        _ = registry["nonexistent_score"]


def test_genomic_scores_registry_contains(
    annotation_gpf: GPFInstance,
) -> None:
    """Test GenomicScoresRegistry __contains__ method."""
    registry = annotation_gpf.genomic_scores
    assert registry is not None

    assert "phastcons100" in registry
    assert "nonexistent_score" not in registry


def test_genomic_scores_registry_len(annotation_gpf: GPFInstance) -> None:
    """Test GenomicScoresRegistry __len__ method."""
    registry = annotation_gpf.genomic_scores
    assert registry is not None

    assert len(registry) == 1


def test_genomic_scores_registry_empty() -> None:
    """Test GenomicScoresRegistry with empty scores dict."""
    registry = GenomicScoresRegistry({})

    assert len(registry) == 0
    assert len(registry.get_scores()) == 0
    assert "anything" not in registry


def test_build_annotator_scores_desc(
    annotation_gpf: GPFInstance,
) -> None:
    """Test GenomicScoresRegistry._build_annotator_scores_desc method."""
    annotation_pipeline = annotation_gpf.get_annotation_pipeline()
    assert annotation_pipeline is not None

    # Find the position_score annotator
    score_annotator = None
    for annotator in annotation_pipeline.annotators:
        if annotator.get_info().type == "position_score":
            score_annotator = annotator
            break

    assert score_annotator is not None

    # Build score descriptions
    score_descs = GenomicScoresRegistry._build_annotator_scores_desc(
        cast(GenomicScoreAnnotatorBase, score_annotator),
    )

    assert len(score_descs) == 1
    assert "phastcons100" in score_descs
    assert isinstance(score_descs["phastcons100"], ScoreDesc)
    assert score_descs["phastcons100"].name == "phastcons100"
