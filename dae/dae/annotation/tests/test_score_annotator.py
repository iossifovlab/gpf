
import numpy
import pyarrow as pa

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.tools.score_annotator import (
    PositionScoreAnnotator,
    NPScoreAnnotator,
)


def test_position_score_annotator(
        phastcons100way_variants_expected,
        anno_grdb, genomes_db_2013):
    resource = anno_grdb.get_resource("hg38/TESTphastCons100way")
    annotator = PositionScoreAnnotator(resource)
    pipeline = AnnotationPipeline(None, None)
    pipeline.add_annotator(annotator)

    for sv, e in phastcons100way_variants_expected:
        pipeline.annotate_summary_variant(sv)

        assert sv.get_attribute("phastCons100way")[0] == e


def test_position_score_annotator_schema(anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTphastCons100way")
    annotator = PositionScoreAnnotator(resource)
    assert annotator is not None

    schema = annotator.annotation_schema
    assert schema is not None


def test_np_score_annotator(cadd_variants_expected, anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    annotator = NPScoreAnnotator(resource)
    pipeline = AnnotationPipeline(None, None)
    pipeline.add_annotator(annotator)

    for sv, e in cadd_variants_expected:
        pipeline.annotate_summary_variant(sv)
        for score, value in e.items():
            assert numpy.isclose(sv.get_attribute(score)[0], value)


def test_np_score_annotator_schema(anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    annotator = NPScoreAnnotator(resource)

    schema = annotator.annotation_schema
    assert schema is not None
    assert isinstance(schema, pa.Schema)
    assert "cadd_raw" in schema.names
    assert "cadd_phred" in schema.names

    field = schema.field("cadd_raw")
    assert field.type == pa.float32()

    field = schema.field("cadd_phred")
    assert field.type == pa.float32()

    assert len(schema) == 2
    print(dir(schema))


def test_np_score_annotator_output_columns(anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    annotator = NPScoreAnnotator(resource)

    output_columns = annotator.output_columns
    assert output_columns == ["cadd_raw", "cadd_phred"]


def test_position_score_annotator_indels(
        phastcons100way_indel_variants_expected,
        anno_grdb, mean_override_phastcons):
    resource = anno_grdb.get_resource("hg38/TESTphastCons100way")
    annotator = PositionScoreAnnotator(
        resource, override=mean_override_phastcons
    )
    pipeline = AnnotationPipeline(None, None)
    pipeline.add_annotator(annotator)

    for sv, e in phastcons100way_indel_variants_expected:
        pipeline.annotate_summary_variant(sv)

        assert sv.get_attribute("phastCons100way")[0] == e


def test_np_score_annotator_indels(
        cadd_indel_variants_expected,
        anno_grdb, mean_override_cadd):
    resource = anno_grdb.get_resource("hg38/TESTCADD")
    annotator = NPScoreAnnotator(
        resource,
        override=mean_override_cadd)
    pipeline = AnnotationPipeline(None, None)
    pipeline.add_annotator(annotator)

    for sv, e in cadd_indel_variants_expected:
        pipeline.annotate_summary_variant(sv)
        for score, value in e.items():
            assert numpy.isclose(sv.get_attribute(score)[0], value)
