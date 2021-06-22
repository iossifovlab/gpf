from dae.annotation.tools.frequency_annotator import FrequencyAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_frequency_annotator(
        frequency_variants_expected, get_score_config, genomes_db_2013):
    config = get_score_config("TESTFreq")
    annotator = FrequencyAnnotator(config, genomes_db_2013)
    pipeline = AnnotationPipeline()
    pipeline.add_annotator(annotator)

    for sv, e in frequency_variants_expected:
        pipeline.annotate_summary_variant(sv)
        for score, value in e.items():
            assert sv.get_attribute(score)[0] == value
