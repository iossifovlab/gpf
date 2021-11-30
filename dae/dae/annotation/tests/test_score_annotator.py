import pytest
from box import Box

from dae.annotation.schema import Schema
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.score_annotator import (
    PositionScoreAnnotator,
    NPScoreAnnotator,
)


def test_position_score_annotator(
        phastcons100way_variants_expected,
        anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTphastCons100way")
    config = Box({
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way"
    })
    annotator = PositionScoreAnnotator(config, resource)
    pipeline = AnnotationPipeline(None, None, None)
    pipeline.add_annotator(annotator)

    for sv, e in phastcons100way_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            assert result.get("phastCons100way") == e


def test_position_score_annotator_schema(anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTphastCons100way")
    config = Box({
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way"
    })
    annotator = PositionScoreAnnotator(
        config,
        resource)
    assert annotator is not None

    schema = annotator.annotation_schema
    assert schema is not None


def test_np_score_annotator(cadd_variants_expected, anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    config = Box({
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD"
    })
    annotator = NPScoreAnnotator(config, resource)
    pipeline = AnnotationPipeline([], anno_grdb, None)
    pipeline.add_annotator(annotator)

    for sv, e in cadd_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            for score, value in e.items():
                assert result.get(score) == pytest.approx(value, abs=1e-2)


def test_np_score_annotator_schema(anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    config = Box({
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD"
    })
    annotator = NPScoreAnnotator(config, resource)

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


def test_np_score_annotator_output_columns(anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    config = Box({
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD"
    })
    annotator = NPScoreAnnotator(config, resource)

    output_columns = annotator.output_columns
    assert output_columns == ["cadd_raw", "cadd_phred"]


def test_position_score_annotator_indels(
        phastcons100way_indel_variants_expected,
        anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTphastCons100way")

    config = Box({
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTphastCons100way",
        "attributes": [{
            'source': 'phastCons100way',
            'destination': 'phastCons100way',
            'position_aggregator': "mean"
        }]
    })
    annotator = PositionScoreAnnotator(config, resource)
    pipeline = AnnotationPipeline([], anno_grdb, None)
    pipeline.add_annotator(annotator)

    for sv, e in phastcons100way_indel_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())

            assert result.get("phastCons100way") == \
                pytest.approx(e, abs=1e-2)


def test_position_score_annotator_mean_aggregate(
    position_agg_mean_variants_expected, anno_grdb
):
    resource = anno_grdb.get_resource("hg38/TESTPosAgg")
    config = Box({
        "annotator_type": "position_score",
        "resource_id": "hg38/TESTPosAgg"
    })
    annotator = PositionScoreAnnotator(config, resource)
    pipeline = AnnotationPipeline([], anno_grdb, None)
    pipeline.add_annotator(annotator)

    for sv, e in position_agg_mean_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())

            assert result.get("test_score") == pytest.approx(e, 1e-2)


def test_np_score_annotator_indels(
        cadd_indel_variants_expected,
        anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    config = Box({
        "annotator_type": "np_score",
        "resource_id": "hg38/TESTCADD",
        "attributes": [
            {
                'source': 'cadd_raw',
                'destination': 'cadd_raw',
            },
            {
                'source': 'cadd_phred',
                'destination': 'cadd_phred',
            }
        ]
    })

    annotator = NPScoreAnnotator(config, resource)

    pipeline = AnnotationPipeline([], anno_grdb, None)
    pipeline.add_annotator(annotator)

    for sv, e in cadd_indel_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            print(sa, sa.get_annotatable())
            for score, value in e.items():
                assert result.get(score) == pytest.approx(value, rel=1e-3)
