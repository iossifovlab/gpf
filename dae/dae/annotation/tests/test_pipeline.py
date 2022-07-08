import pytest

from dae.genomic_resources.genomic_scores import \
    open_position_score_from_resource
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.score_annotator import PositionScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_build_pipeline(
        annotation_config, grr_fixture):

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config,
        grr_repository=grr_fixture)

    assert len(pipeline.annotators) == 5


def test_build_pipeline_schema(
        annotation_config, grr_fixture):

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config,
        grr_repository=grr_fixture)

    schema = pipeline.annotation_schema
    assert schema is not None

    # assert len(schema) == 10

    assert "gene_effects" in schema.names
    field = schema["gene_effects"]
    print(field, dir(field))

    assert field.type == "str", field

    assert "cadd_raw" in schema.names
    field = schema["cadd_raw"]
    assert field.type == "float"
