# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.annotation.clinvar_annotator import ClinVarAnnotator
from dae.annotation.annotatable import VCFAllele


@pytest.fixture(scope="session")
def clinvar_annotator_config():
    config = {
        "annotator_type": "clinvar_annotator",
        "resource_id": "clinvar",
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
    return ClinVarAnnotator.validate_config(config)


@pytest.fixture(scope="function")
def clinvar_annotator(grr_fixture, clinvar_annotator_config):
    resource = grr_fixture.get_resource("clinvar")
    return ClinVarAnnotator(clinvar_annotator_config, resource)


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


def test_clinvar_annotator(clinvar_annotator, test_annotatables_expected):
    for annotatable, expected in test_annotatables_expected:
        context = {}
        result = clinvar_annotator.annotate(annotatable, context)
        assert result == expected
