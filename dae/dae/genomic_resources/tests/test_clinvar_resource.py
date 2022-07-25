# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import pysam
from dae.genomic_resources.clinvar import ClinVarVcf


@pytest.fixture(scope="function")
def clinvar_fixtures(grr_fixture, grr_http):
    local = ClinVarVcf(grr_fixture.get_resource("clinvar"))
    local.open()
    http = ClinVarVcf(grr_http.get_resource("clinvar"))
    http.open()
    return {
        "local": local,
        "http": http
    }


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_clinvarvcf_init(clinvar_fixtures, resource_type):
    # pylint: disable=no-member
    clinvar_vcf = clinvar_fixtures[resource_type]
    assert isinstance(clinvar_vcf.vcf, pysam.VariantFile)


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_clinvar_vcf_get_variant_info(clinvar_fixtures, resource_type):
    clinvar_vcf = clinvar_fixtures[resource_type]
    info = clinvar_vcf.get_variant_info("1", 925952)
    assert len(info) == 2
    assert info == {
        "ALLELEID": 1003021,
        "GENEINFO": "SAMD11:148398"
    }


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_clinvar_vcf_get_header_info(clinvar_fixtures, resource_type):
    clinvar_vcf = clinvar_fixtures[resource_type]
    header = clinvar_vcf.get_header_info()
    assert len(header) == 2
    print(header)
    assert header == {
        "ALLELEID": {
            "name": "ALLELEID",
            "type": "Integer",
            "number": 1,
            "description": "the ClinVar Allele ID"
        },
        "GENEINFO": {
            "name": "GENEINFO",
            "type": "String",
            "number": 1,
            "description": (
                "Gene(s) for the variant reported "
                "as gene symbol:gene id. The gene "
                "symbol and id are delimited by a "
                "colon (:) and each pair is delimited by a vertical bar (|)"
            )
        }
    }


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_close(clinvar_fixtures, resource_type):
    clinvar_vcf = clinvar_fixtures[resource_type]
    clinvar_vcf.close()
