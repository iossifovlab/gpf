# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import pysam
from dae.genomic_resources.vcf_info_resource import VcfInfoResource


@pytest.fixture(scope="function")
def vcf_info_fixtures(grr_fixture, grr_http):
    local = VcfInfoResource(grr_fixture.get_resource("clinvar"))
    local.open()
    http = VcfInfoResource(grr_http.get_resource("clinvar"))
    http.open()
    return {
        "local": local,
        "http": http
    }


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_vcf_info_resource_vcf_init(vcf_info_fixtures, resource_type):
    # pylint: disable=no-member
    clinvar_vcf_info = vcf_info_fixtures[resource_type]
    assert isinstance(clinvar_vcf_info.vcf, pysam.VariantFile)


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_vcf_info_resource_vcf_get_variant_info(
        vcf_info_fixtures, resource_type):
    clinvar_vcf_info = vcf_info_fixtures[resource_type]
    info = clinvar_vcf_info.get_variant_info("1", 925952)
    assert len(info) == 2
    assert info == {
        "ALLELEID": 1003021,
        "GENEINFO": "SAMD11:148398"
    }


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_vcf_info_resource_vcf_get_header_info(
        vcf_info_fixtures, resource_type):
    clinvar_vcf_info = vcf_info_fixtures[resource_type]
    header = clinvar_vcf_info.get_header_info()
    assert len(header) == 2
    print(header)
    alleleid = header["ALLELEID"]
    assert alleleid.score_id == "ALLELEID"
    assert alleleid.type == "int"
    assert alleleid.description == "the ClinVar Allele ID"

    geneinfo = header["GENEINFO"]
    assert geneinfo.score_id == "GENEINFO"
    assert geneinfo.type == "str"
    assert geneinfo.description == (
        "Gene(s) for the variant reported "
        "as gene symbol:gene id. The gene "
        "symbol and id are delimited by a "
        "colon (:) and each pair is delimited by a vertical bar (|)"
    )


@pytest.mark.parametrize("resource_type", ["local", "http"])
def test_close(vcf_info_fixtures, resource_type):
    clinvar_vcf_info = vcf_info_fixtures[resource_type]
    clinvar_vcf_info.close()
