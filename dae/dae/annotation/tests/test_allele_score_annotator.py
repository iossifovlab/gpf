from dae.annotation.tools.allele_score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_allele_score_annotator(
        frequency_variants_expected, anno_grdb):
    resource = anno_grdb.get_resource("hg38/TESTFreq")
    annotator = AlleleScoreAnnotator(resource)
    pipeline = AnnotationPipeline(None, None)
    pipeline.add_annotator(annotator)

    for sv, e in frequency_variants_expected:
        for sa in sv.alt_alleles:
            result = pipeline.annotate_allele(sa)
            for score, value in e.items():
                assert result.get(score) == value
