# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.genomic_resources.genomic_scores import \
    build_np_score_from_resource, \
    build_position_score_from_resource
from dae.annotation.schema import Schema
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.score_annotator import (
    PositionScoreAnnotator,
    NPScoreAnnotator,
)


def test_position_score_annotator(
        phastcons100way_variants_expected,
        grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTphastCons100way")
    config = {
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way"
    }
    score = build_position_score_from_resource(resource)
    score.open()

    annotator = PositionScoreAnnotator(config, score)
    pipeline = AnnotationPipeline([], grr_fixture)
    pipeline.add_annotator(annotator)

    for sv, expect in phastcons100way_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            assert result.get("phastCons100way") == expect


def test_position_score_annotator_schema(grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTphastCons100way")
    config = {
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way"
    }
    score = build_position_score_from_resource(resource)
    score.open()

    annotator = PositionScoreAnnotator(
        config,
        score)
    assert annotator is not None

    schema = annotator.annotation_schema
    assert schema is not None


def test_np_score_annotator(cadd_variants_expected, grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTCADD")
    config = {
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD"
    }
    score = build_np_score_from_resource(resource)
    score.open()
    annotator = NPScoreAnnotator(config, score)
    pipeline = AnnotationPipeline([], grr_fixture)
    pipeline.add_annotator(annotator)

    for sv, expect in cadd_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            for score, value in expect.items():
                assert result.get(score) == pytest.approx(value, abs=1e-2)


def test_np_score_annotator_schema(grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTCADD")
    config = {
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD"
    }
    score = build_np_score_from_resource(resource)
    score.open()
    annotator = NPScoreAnnotator(config, score)

    schema = annotator.annotation_schema
    assert schema is not None
    assert isinstance(schema, Schema)
    assert "cadd_raw" in schema.names
    assert "cadd_phred" in schema.names

    field = schema["cadd_raw"]
    assert field.type == "float"

    field = schema["cadd_phred"]
    assert field.type == "float"

    assert len(schema) == 2
    print(dir(schema))


def test_position_score_annotator_indels(
        phastcons100way_indel_variants_expected,
        grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTphastCons100way")

    config = {
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way",
        "attributes": [{
            "source": "phastCons100way",
            "destination": "phastCons100way",
            "position_aggregator": "mean"
        }]
    }
    score = build_position_score_from_resource(resource)
    score.open()

    annotator = PositionScoreAnnotator(config, score)
    pipeline = AnnotationPipeline([], grr_fixture)
    pipeline.add_annotator(annotator)

    for sv, expect in phastcons100way_indel_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())

            assert result.get("phastCons100way") == \
                pytest.approx(expect, abs=1e-2)


def test_position_score_annotator_mean_aggregate(
    position_agg_mean_variants_expected, grr_fixture
):
    resource = grr_fixture.get_resource("hg38/TESTPosAgg")
    config = {
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTPosAgg"
    }
    score = build_position_score_from_resource(resource)
    score.open()

    annotator = PositionScoreAnnotator(config, score)
    pipeline = AnnotationPipeline([], grr_fixture)
    pipeline.add_annotator(annotator)

    for sv, expect in position_agg_mean_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())

            assert result.get("test_score") == pytest.approx(expect, 1e-2)


def test_np_score_annotator_indels(
        cadd_indel_variants_expected,
        grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTCADD")
    config = {
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD",
        "attributes": [
            {
                "source": "cadd_raw",
                "destination": "cadd_raw",
            },
            {
                "source": "cadd_phred",
                "destination": "cadd_phred",
            }
        ]
    }
    score = build_np_score_from_resource(resource)
    score.open()
    annotator = NPScoreAnnotator(config, score)

    pipeline = AnnotationPipeline([], grr_fixture)
    pipeline.add_annotator(annotator)

    for sv, expect in cadd_indel_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            print(sa, sa.get_annotatable())
            for score, value in expect.items():
                assert result.get(score) == pytest.approx(value, rel=1e-3)


def test_score_annotator_resource_files(grr_fixture):
    resource = grr_fixture.get_resource("hg38/TESTphastCons100way")
    config = {
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way"
    }
    score = build_position_score_from_resource(resource)
    score.open()

    annotator = PositionScoreAnnotator(config, score)
    assert annotator.resource_files == {
        "hg38/TESTphastCons100way": {"TESTphastCons100way.bedGraph.gz",
                                     "TESTphastCons100way.bedGraph.gz.tbi"}
    }
