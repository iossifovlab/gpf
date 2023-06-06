# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.annotation.annotation_factory import build_annotation_pipeline
import pytest


def test_position_score_annotator(
        phastcons100way_variants_expected,
        grr_fixture):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - position_score: hg38/TESTphastCons100way
        """, grr_repository=grr_fixture)

    for sv, expect in phastcons100way_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            assert result.get("phastCons100way") == expect


def test_position_score_annotator_schema(grr_fixture):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - position_score: hg38/TESTphastCons100way
        """, grr_repository=grr_fixture)

    assert len(pipeline.annotators[0].attributes) > 0


def test_np_score_annotator(cadd_variants_expected, grr_fixture):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - np_score: hg38/TESTCADD
        """, grr_repository=grr_fixture)

    for sv, expect in cadd_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            for score, value in expect.items():
                assert result.get(score) == pytest.approx(value, abs=1e-2)


def test_np_score_annotator_schema(grr_fixture):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - np_score: hg38/TESTCADD
        """, grr_repository=grr_fixture)

    assert len(pipeline.get_attributes()) == 2

    attribute = pipeline.get_attribute_info("cadd_raw")
    assert attribute is not None
    assert attribute.type == "float"

    attribute = pipeline.get_attribute_info("cadd_phred")
    assert attribute is not None
    assert attribute.type == "float"


def test_position_score_annotator_indels(
        phastcons100way_indel_variants_expected,
        grr_fixture):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - position_score:
                resource_id: hg38/TESTphastCons100way
                attributes:
                - destination: phastCons100way
                  source: phastCons100way
                  position_aggregator: mean
        """, grr_repository=grr_fixture)

    for sv, expect in phastcons100way_indel_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())

            assert result.get("phastCons100way") == \
                pytest.approx(expect, abs=1e-2)


def test_position_score_annotator_mean_aggregate(
    position_agg_mean_variants_expected, grr_fixture
):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - position_score: hg38/TESTPosAgg
        """, grr_repository=grr_fixture)

    for sv, expect in position_agg_mean_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())

            assert result.get("test_score") == pytest.approx(expect, 1e-2)


def test_np_score_annotator_indels(
        cadd_indel_variants_expected,
        grr_fixture):
    
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - np_score:
                resource_id: hg38/TESTCADD
                attributes:
                - cadd_raw
                - cadd_phred
        """, grr_repository=grr_fixture)
    
    for sv, expect in cadd_indel_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate(sa.get_annotatable())
            print(sa, sa.get_annotatable())
            for score, value in expect.items():
                assert result.get(score) == pytest.approx(value, rel=1e-3)


def test_score_annotator_resources(grr_fixture):
    pipeline = build_annotation_pipeline(
        pipeline_config_str="""
            - position_score: hg38/TESTphastCons100way
        """, grr_repository=grr_fixture)

    assert pipeline.get_resource_ids() == {"hg38/TESTphastCons100way"}
