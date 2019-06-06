'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest
from RegionOperations import Region
from utils.vcf_utils import mat2str


@pytest.mark.parametrize("region,count,freq0,freq1", [
    (Region('1', 11539, 11539), 2, 75.0, 25.0),
    (Region('1', 11540, 11540), 2, 75.0, 25.0),
    (Region('1', 11541, 11541), 2, 87.5, 12.5),
    (Region('1', 11542, 11542), 2, 87.5, 12.5),
    (Region('1', 11550, 11550), 2, 100.0, 0.0),
    (Region('1', 11553, 11553), 2, 100.0, 0.0),
    (Region('1', 11551, 11551), 2, 0.0, 100.0),
    (Region('1', 11552, 11552), 2, 0.0, 100.0),
])
def test_variant_frequency_single(variants_vcf, region, count, freq0, freq1):
    fvars = variants_vcf("backends/trios2")
    vs = list(fvars.query_variants(
        regions=[region],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st))
        print(v.frequencies)

        assert freq0 == pytest.approx(v.frequencies[0], 1e-2)
        if len(v.frequencies) == 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2)


@pytest.mark.parametrize("region,count,freq0,freq1,freq2", [
    (Region('1', 11600, 11600), 2, 100.0, 0.0, 0.0),
    (Region('1', 11601, 11601), 2, 75.0, 25.0, 0.0),
    (Region('1', 11604, 11604), 2, 75.0, 25.0, 0.0),
    (Region('1', 11602, 11602), 2, 75.0, 0.0, 25.0),
    (Region('1', 11605, 11605), 2, 50.0, 25.0, 25.0),
    (Region('1', 11603, 11603), 2, 75.0, 0.0, 25.0),
])
def test_variant_frequency_multi_alleles(
        variants_vcf, region, count, freq0, freq1, freq2):

    fvars = variants_vcf("backends/trios2")
    vs = list(fvars.query_variants(
        regions=[region],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st))
        print(v.frequencies)
        # assert len(v.frequencies) == 3

        assert freq0 == pytest.approx(v.frequencies[0], 1e-2)
        if len(v.frequencies) == 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2) or \
                freq2 == pytest.approx(v.frequencies[1], 1e-2)
        elif len(v.frequencies) > 2:
            assert freq1 == pytest.approx(v.frequencies[1], 1e-2)
            assert freq2 == pytest.approx(v.frequencies[2], 1e-2)
