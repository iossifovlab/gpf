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
def test_variant_attr(full_vcf, region, count, freq0, freq1):
    fvars = full_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        regions=[region]))
    assert len(vs) == count
    for v in vs:
        assert v.atts is not None
        assert len(v.atts['all.nAltAlls']) == 1
        assert len(v.atts['all.nRefAlls']) == 1

        assert freq0 == pytest.approx(v['all.refFreq'][1], 1e-2)
        assert freq1 == pytest.approx(v['all.altFreq'][1], 1e-2)


@pytest.mark.parametrize("region,count,freq0,freq1,freq2", [
    (Region('1', 11600, 11600), 2, 100.0, 0.0, 0.0),
    (Region('1', 11601, 11601), 2, 75.0, 25.0, 0.0),
])
def test_variant_attr_multi_alleles(
        full_vcf, region, count, freq0, freq1, freq2):

    fvars = full_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        regions=[region]))
    assert len(vs) == count

    for v in vs:

        assert len(v.atts['all.nAltAlls']) == 2
        assert len(v.atts['all.nRefAlls']) == 2
        assert len(v['all.nRefAlls']) == 2

        assert v['all.refFreq'][1] == pytest.approx(freq0, 1e-2)
        assert v['all.altFreq'][1] == pytest.approx(freq1, 1e-2)

        assert v['all.refFreq'][2] == pytest.approx(freq0, 1e-2)
        assert v['all.altFreq'][2] == pytest.approx(freq2, 1e-2)

        assert v.get_attr('all.refFreq')[1] == pytest.approx(freq0, 1e-2)
        assert v.get_attr('all.altFreq')[1] == pytest.approx(freq1, 1e-2)

        assert v.atts['all.refFreq'][2] == pytest.approx(freq0, 1e-2)
        assert v.atts['all.altFreq'][2] == pytest.approx(freq2, 1e-2)

        assert v.has_attr('all.nAltAlls')
        assert 'all.nAltAlls' in v

        assert v.summary.has_attr('all.nAltAlls')
        assert 'all.nAltAlls' in v.summary

        assert v.has_attr('all.nRefAlls')
        assert 'all.nRefAlls' in v

        assert v.summary.has_attr('all.nRefAlls')
        assert 'all.nRefAlls' in v.summary
