# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.annotation.annotatable import VCFAllele
from dae.annotation.score_annotator import AlleleScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotatorInfo, \
    AnnotationPipeline
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.genomic_resources.testing import \
    setup_directories, convert_to_tab_separated
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources import build_genomic_resource_repository


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


@pytest.mark.parametrize("variant, expected", [
    (("1", 10, "A", "G"), 0.02),
    (("1", 10, "A", "C"), 0.03),
    (("1", 10, "A", "T"), 0.04),
    (("1", 16, "C", "T"), 0.04),
    (("1", 16, "C", "A"), 0.05),
])
def test_allele_score_with_default_score_annotation(
        variant, expected, tmp_path_factory):
    root_path = tmp_path_factory.mktemp("allele_score_annotation")
    setup_directories(
        root_path / "grr", {
            "allele_score": {
                GR_CONF_FILE_NAME: """
                    type: allele_score
                    table:
                        filename: data.txt
                        reference:
                          name: reference
                        alternative:
                          name: alternative
                    scores:
                        - id: ID
                          type: str
                          desc: "variant ID"
                          name: ID
                        - id: freq
                          type: float
                          desc: ""
                          name: freq
                    default_annotation:
                      attributes:
                      - source: freq
                        destination: allele_freq

                """,
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  reference  alternative ID  freq
                    1      10         A          G           ag  0.02
                    1      10         A          C           ac  0.03
                    1      10         A          T           at  0.04
                    1      16         CA         G           .   0.03
                    1      16         C          T           ct  0.04
                    1      16         C          A           ca  0.05
                """)
            }
        })
    local_repo = build_genomic_resource_repository({
        "id": "allele_score_local",
        "type": "directory",
        "directory": str(root_path / "grr")
    })
    annotation_configuration = textwrap.dedent("""
        - allele_score:
            resource_id: allele_score
    """)
    pipeline = build_annotation_pipeline(
        pipeline_config_str=annotation_configuration,
        grr_repository=local_repo)

    annotatable = VCFAllele(*variant)
    result = pipeline.annotate(annotatable)
    assert len(result) == 1
    assert result["allele_freq"] == expected
