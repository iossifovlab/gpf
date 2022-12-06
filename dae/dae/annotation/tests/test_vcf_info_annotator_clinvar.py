# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.genomic_resources.genomic_scores import AlleleScore
from dae.annotation.vcf_info_annotator import VcfInfoAnnotator
from dae.annotation.annotatable import VCFAllele


@pytest.fixture(scope="session")
def vcf_info_annotator_config():
    config = {
        "annotator_type": "vcf_info",
        "resource_id": "vcf_info",
        "attributes": [
            {
                "source": "ALLELEID",
                "destination": "ALLELEID"
            },
            {
                "source": "GENEINFO",
                "destination": "GENEINFO"
            },
        ]
    }
    return VcfInfoAnnotator.validate_config(config)


@pytest.fixture(scope="function")
def vcf_info_annotator(grr_fixture, vcf_info_annotator_config):
    resource = grr_fixture.get_resource("clinvar")
    vcf_info = AlleleScore(resource)
    annotator = VcfInfoAnnotator(vcf_info_annotator_config, vcf_info)
    annotator.open()
    return annotator


@pytest.mark.parametrize("vcf_allele,expected", [
    (
        VCFAllele("1", 925952, "G", "A"),
        {
            "ALLELEID": 1003021,
            "GENEINFO": "SAMD11:148398"
        }
    ),
    (
        VCFAllele("1", 925952, "G", "C"),
        {
            "ALLELEID": None,
            "GENEINFO": None,
        }
    ),
    (
        VCFAllele("1", 925953, "G", "C"),
        {
            "ALLELEID": None,
            "GENEINFO": None,
        }
    ),
    (
        VCFAllele("1", 925969, "C", "T"),
        {
            "ALLELEID": 1600580,
            "GENEINFO": "SAMD11:148398"
        }
    ),
    (
        VCFAllele("1", 925969, "G", "C"),
        {
            "ALLELEID": None,
            "GENEINFO": None,
        }
    ),
    (
        VCFAllele("1", 925976, "T", "C"),
        {
            "ALLELEID": 1396033,
            "GENEINFO": "SAMD11:148398"
        }
    ),
    (
        VCFAllele("1", 925976, "C", "G"),
        {
            "ALLELEID": None,
            "GENEINFO": None,
        }
    ),
])
def test_vcf_info_annotator(
        vcf_info_annotator, vcf_allele, expected):
    context = {}
    result = vcf_info_annotator.annotate(vcf_allele, context)
    assert result == expected
