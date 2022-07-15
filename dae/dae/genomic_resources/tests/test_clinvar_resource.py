# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from pysam import VariantFile
from dae.genomic_resources.clinvar import ClinVarVcf


@pytest.fixture(scope="function")
def clinvar_vcf(grr_fixture):
    return ClinVarVcf(grr_fixture.get_resource("clinvar"))


def test_clinvarvcf_init(clinvar_vcf):
    assert isinstance(clinvar_vcf.vcf, VariantFile)


def test_clinvar_vcf_get_variant_info(clinvar_vcf):
    info = clinvar_vcf.get_variant_info("1", 925952)
    assert len(info) == 2
    assert info == {
        "ALLELEID": 1003021,
        "GENEINFO": "SAMD11:148398"
    }


def test_clinvar_vcf_get_header_info(clinvar_vcf):
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


def test_close(clinvar_vcf):
    clinvar_vcf.close()
    assert clinvar_vcf.vcf.closed is True
