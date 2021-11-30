from box import Box
from dae.annotation.score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_allele_score_annotator(
        frequency_variants_expected, anno_grdb):

    pipeline = AnnotationPipeline([], anno_grdb, None)

    annotator = AlleleScoreAnnotator(Box({
        "annotator_type": "allele_score",
        "resource_id": "hg38/TESTFreq",
        "attributes": None,
    }), anno_grdb.get_resource("hg38/TESTFreq"))
    pipeline.add_annotator(annotator)

    for sv, e in frequency_variants_expected:
        for sa in sv.alt_alleles:
            a = sa.get_annotatable()
            result = pipeline.annotate(a)
            for score, value in e.items():
                assert result.get(score) == value
