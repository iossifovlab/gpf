'''
Created on Mar 30, 2018

@author: lubo
'''
import pytest
from RegionOperations import Region


@pytest.mark.parametrize("region,count,freq0,freq1", [
    (Region('1', 11539, 11539), 2, 75.0, 25.0),
    (Region('1', 11540, 11540), 2, 75.0, 25.0),
])
def test_variant_attr(variants_vcf, region, count, freq0, freq1):
    fvars = variants_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        regions=[region]))
    assert len(vs) == count
    for v in vs:
        assert len(v.get_attribute('af_alternative_allele_count')) <= 2
        assert len(v.get_attribute('af_reference_allele_count')) <= 2

#         assert freq0 == pytest.approx(v['all.refFreq'][1], 1e-2)
#         assert freq1 == pytest.approx(v['all.altFreq'][1], 1e-2)


@pytest.mark.parametrize("region,count,freq0,freq1,freq2", [
    (Region('1', 11600, 11600), 2, 100.0, 0.0, 0.0),
    (Region('1', 11601, 11601), 2, 75.0, 25.0, 0.0),
])
def test_variant_attr_multi_alleles(
        variants_vcf, region, count, freq0, freq1, freq2):

    fvars = variants_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        regions=[region]))
    assert len(vs) == count

    for v in vs:

        assert len(v.get_attribute('af_alternative_allele_count')) <= 2
        assert len(v.get_attribute('af_reference_allele_count')) <= 2
#         assert len(v['af_reference_allele_count']) == 2
#
#         assert v['af_reference_allele_freq'][1] == pytest.approx(freq0, 1e-2)
#         assert v['af_alternative_allele_freq'][1] == pytest.approx(freq1, 1e-2)

#         assert v['af_reference_allele_freq'][2] == pytest.approx(freq0, 1e-2)
#         assert v['af_alternative_allele_freq'][2] == pytest.approx(freq2, 1e-2)
