'''
Created on Mar 30, 2018

@author: lubo
'''
import pytest

from dae.RegionOperations import Region


@pytest.mark.parametrize("region,count,freq0,freq1", [
    (Region('1', 11501, 11501), 1, 75.0, 25.0),
    (Region('1', 11503, 11503), 1, 75.0, 25.0),
    (Region('1', 11511, 11511), 1, 50.0, 50.0),
    (Region('1', 11515, 11515), 1, 75.0, 25.0),
])
def test_variant_attributes(variants_vcf, region, count, freq0, freq1):
    fvars = variants_vcf("backends/inheritance_trio")
    vs = list(fvars.query_variants(
        regions=[region]))
    assert len(vs) == count
    for v in vs:
        assert len(v.get_attribute('af_allele_count')) == 2
        assert len(v.get_attribute('af_allele_freq')) == 2

        freq = v['af_allele_freq']

        assert freq0 == pytest.approx(freq[0], 1e-2)
        assert freq1 == pytest.approx(freq[1], 1e-2)

        assert [None, None] == v.get_attribute("ala bala")
