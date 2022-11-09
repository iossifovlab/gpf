# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.annotation.vcf_info_annotator import VcfInfoAnnotator
from dae.annotation.annotatable import VCFAllele


@pytest.fixture(scope="session")
def vcf_info_annotator_config():
    config = {
        "annotator_type": "vcf_info_annotator",
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
    annotator = VcfInfoAnnotator(vcf_info_annotator_config, resource)
    annotator.open()
    return annotator


@pytest.fixture(scope="session")
def test_annotatables_expected():
    return [
        (
            VCFAllele("1", 925952, "G", "C"),
            {
                "ALLELEID": 1003021,
                "GENEINFO": "SAMD11:148398"
            }
        ),
        (
            VCFAllele("1", 925953, "G", "C"),
            {}
        ),
        (
            VCFAllele("1", 925969, "G", "C"),
            {
                "ALLELEID": 1600580,
                "GENEINFO": "SAMD11:148398"
            }
        ),
        (
            VCFAllele("1", 925976, "G", "C"),
            {
                "ALLELEID": 1396033,
                "GENEINFO": "SAMD11:148398"
            }
        )
    ]


def test_vcf_info_annotator(vcf_info_annotator, test_annotatables_expected):
    for annotatable, expected in test_annotatables_expected:
        context = {}
        result = vcf_info_annotator.annotate(annotatable, context)
        assert result == expected
