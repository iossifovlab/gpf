'''
Created on Sep 26, 2016

@author: lubo
'''
from query_variants import validate_region, fix_region


def test_gene_region_simple():
    regions = "1:10-1000"
    assert validate_region(regions)

    regions = "chr1:10-1000"
    assert validate_region(regions)

    regions = "chr1:10,000-1,000,000"
    assert validate_region(regions)


def test_fix_region_simple():
    regions = "1:10-1000"
    assert "1:10-1000" == fix_region(regions)

    regions = "chr1:10-1000"
    assert "1:10-1000" == fix_region(regions)

    regions = "chr1:10,000-1,000,000"
    assert "1:10000-1000000" == fix_region(regions)
