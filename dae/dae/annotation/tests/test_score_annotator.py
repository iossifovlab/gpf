import numpy
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.tools.score_annotator import (
    PositionScoreAnnotator,
    NPScoreAnnotator,
)


def test_position_score_annotator(
        phastcons100way_variants_expected,
        anno_grdb, genomes_db_2013):
    from dae.configuration.gpf_config_parser import FrozenBox
    config = FrozenBox({
        "annotator": "position_score",
        "resource": "hg38/TESTphastCons100way",
    })
    annotator = PositionScoreAnnotator(config, genomes_db_2013, anno_grdb)
    pipeline = AnnotationPipeline()
    pipeline.add_annotator(annotator)

    for sv, e in phastcons100way_variants_expected:
        pipeline.annotate_summary_variant(sv)

        assert sv.get_attribute("phastCons100way")[0] == e


def test_np_score_annotator(
        cadd_variants_expected, get_score_config, genomes_db_2013):
    config = get_score_config("TESTCADD")
    annotator = NPScoreAnnotator(config, genomes_db_2013)
    pipeline = AnnotationPipeline()
    pipeline.add_annotator(annotator)

    for sv, e in cadd_variants_expected:
        pipeline.annotate_summary_variant(sv)
        for score, value in e.items():
            assert numpy.isclose(sv.get_attribute(score)[0], value)
