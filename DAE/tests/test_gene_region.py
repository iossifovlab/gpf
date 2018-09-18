'''
Created on Sep 26, 2016

@author: lubo
'''
from __future__ import unicode_literals
from query_variants import validate_region, fix_region


def test_gene_region_simple():
    regions = "1:10-1000"
    assert validate_region(regions)

    regions = "chr1:10-1000"
    assert validate_region(regions)

    regions = "chr1:10,000-1,000,000"
    assert validate_region(regions)

    regions = '1:-'
    assert not validate_region(regions)


def test_fix_region_simple():
    regions = "1:10-1000"
    assert "1:10-1000" == fix_region(regions)

    regions = "chr1:10-1000"
    assert "1:10-1000" == fix_region(regions)

    regions = "chr1:10,000-1,000,000"
    assert "1:10000-1000000" == fix_region(regions)


def test_gene_region_single():
    regions = "1:10"
    assert validate_region(regions)

    assert "1:10-10" == fix_region(regions)

    regions = "chr1:10,000"
    assert "1:10000-10000" == fix_region(regions)
