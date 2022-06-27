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


@pytest.mark.xfail()
def test_internal_attribute_filtered(
        phastcons100way_indel_variants_expected,
        grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTphastCons100way")

    config = {
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way",
        "attributes": [{
            "source": "phastCons100way",
            "destination": "phastCons100way",
            "position_aggregator": "mean",
            "internal": True
        }]
    }
    score = open_position_score_from_resource(resource)

    annotator = PositionScoreAnnotator(config, score)
    pipeline = AnnotationPipeline([], grr_fixture)
    pipeline.add_annotator(annotator)

    variant = phastcons100way_indel_variants_expected[0][0]
    allele = variant.alt_alleles[0]

    result = pipeline.annotate(allele.get_annotatable())
    assert "phastCons100way" not in result
