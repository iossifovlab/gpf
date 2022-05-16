from dae.genomic_resources.genomic_scores import \
    open_allele_score_from_resource
from dae.annotation.score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline


def test_allele_score_annotator(
        frequency_variants_expected, grr_fixture):

    pipeline = AnnotationPipeline([], grr_fixture)
    resource = grr_fixture.get_resource("hg38/TESTFreq")
    score = open_allele_score_from_resource(resource)

    annotator = AlleleScoreAnnotator({
        "annotator_type": "allele_score",
        "resource_id": "hg38/TESTFreq",
        "attributes": None,
    }, score)

    pipeline.add_annotator(annotator)

    print(annotator.get_all_annotation_attributes())

    for sv, e in frequency_variants_expected:
        for sa in sv.alt_alleles:
            a = sa.get_annotatable()
            result = pipeline.annotate(a)
            for score, value in e.items():
                assert result.get(score) == value


def test_allele_score_annotator_attributes(
        frequency_variants_expected, grr_fixture):

    pipeline = AnnotationPipeline([], grr_fixture)
    resource = grr_fixture.get_resource("hg38/TESTFreq")
    score = open_allele_score_from_resource(resource)

    annotator = AlleleScoreAnnotator({
        "annotator_type": "allele_score",
        "resource_id": "hg38/TESTFreq",
        "attributes": None,
    }, score)
    pipeline.add_annotator(annotator)

    print(annotator.get_all_annotation_attributes())

    assert annotator.get_all_annotation_attributes() == [
        {"name": "altFreq", "type": "float", "desc": ""},
        {"name": "altFreq2", "type": "float", "desc": ""},
    ]
