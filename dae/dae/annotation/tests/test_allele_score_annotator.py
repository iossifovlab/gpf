# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.annotation.score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import AnnotatorInfo


def test_allele_score_annotator(frequency_variants_expected, grr_fixture):
    pipeline = AnnotationPipeline(grr_fixture)
    annotator = AlleleScoreAnnotator(
        pipeline, AnnotatorInfo("allele_score", [],
                                {"resource_id": "hg38/TESTFreq"}))
    pipeline.add_annotator(annotator)

    with pipeline.open() as work_pipeline:
        for svar, expected in frequency_variants_expected:
            for sallele in svar.alt_alleles:
                annotatable = sallele.get_annotatable()
                result = work_pipeline.annotate(annotatable)
                for score, value in expected.items():
                    assert result.get(score) == value


def test_allele_score_annotator_attributes(grr_fixture):

    pipeline = AnnotationPipeline(grr_fixture)
    annotator = AlleleScoreAnnotator(
        pipeline, AnnotatorInfo("allele_score", [],
                                {"resource_id": "hg38/TESTFreq"}))
    pipeline.add_annotator(annotator)

    assert not annotator.is_open()

    attributes = annotator.get_info().attributes
    assert len(attributes) == 2
    assert attributes[0].name == "alt_freq"
    assert attributes[0].source == "altFreq"
    assert attributes[0].type == "float"
    assert attributes[0].description == ""

    assert attributes[1].name == "alt_freq2"
    assert attributes[1].source == "altFreq2"
    assert attributes[1].type == "float"
    assert attributes[1].description == ""
