# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region


@pytest.mark.parametrize(
    "region,count,ref_freq,alt_freq",
    [
        (Region("1", 11501, 11501), 1, 75.0, 25.0),
        (Region("1", 11503, 11503), 1, 75.0, 25.0),
        (Region("1", 11511, 11511), 1, 50.0, 50.0),
        (Region("1", 11515, 11515), 1, 75.0, 25.0),
    ],
)
def test_variant_attributes(variants_vcf, region, count, ref_freq, alt_freq):
    fvars = variants_vcf("backends/inheritance_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        assert len(v.get_attribute("af_allele_count")) == 1
        assert len(v.get_attribute("af_allele_freq")) == 1

        rfreq = v["af_ref_allele_freq"]
        afreq = v["af_allele_freq"]

        assert ref_freq == pytest.approx(rfreq[0], 1e-2)
        assert alt_freq == pytest.approx(afreq[0], 1e-2)

        assert [None] == v.get_attribute("ala bala")
