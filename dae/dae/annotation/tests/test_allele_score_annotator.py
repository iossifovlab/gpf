# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genomic_resources.genomic_scores import \
    build_allele_score_from_resource
from dae.annotation.score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_allele_score_annotator(
        frequency_variants_expected, grr_fixture):

    pipeline = AnnotationPipeline([], grr_fixture)
    resource = grr_fixture.get_resource("hg38/TESTFreq")
    score = build_allele_score_from_resource(resource)

    annotator = AlleleScoreAnnotator({
        "annotator_type": "allele_score",
        "resource_id": "hg38/TESTFreq",
        "attributes": None,
    }, score)

    pipeline.add_annotator(annotator)

    with pipeline.open() as work_pipeline:

        for svar, expected in frequency_variants_expected:
            for sallele in svar.alt_alleles:
                annotatable = sallele.get_annotatable()
                result = work_pipeline.annotate(annotatable)
                for score, value in expected.items():
                    assert result.get(score) == value


def test_allele_score_annotator_attributes(
        frequency_variants_expected, grr_fixture):

    pipeline = AnnotationPipeline([], grr_fixture)
    resource = grr_fixture.get_resource("hg38/TESTFreq")
    score = build_allele_score_from_resource(resource)

    annotator = AlleleScoreAnnotator({
        "annotator_type": "allele_score",
        "resource_id": "hg38/TESTFreq",
        "attributes": None,
    }, score)

    pipeline.add_annotator(annotator)

    assert annotator.get_all_annotation_attributes() == [
        {"name": "altFreq", "type": "float", "desc": ""},
        {"name": "altFreq2", "type": "float", "desc": ""},
    ]

    assert not annotator.is_open()
