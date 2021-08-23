from dae.annotation.tools.allele_score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_allele_score_annotator(
        frequency_variants_expected, anno_grdb, genomes_db_2013):
    resource = anno_grdb.get_resource("hg38/TESTFreq")
    annotator = AlleleScoreAnnotator(resource, genomes_db_2013)
    pipeline = AnnotationPipeline(None, None, None)
    pipeline.add_annotator(annotator)

    for sv, e in frequency_variants_expected:
        pipeline.annotate_summary_variant(sv)
        for score, value in e.items():
            assert sv.get_attribute(score)[0] == value
