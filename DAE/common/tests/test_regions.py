'''
Created on Feb 20, 2017

@author: lubo
'''
from __future__ import unicode_literals
from common.query_base import RegionsMixin

regions = [
    "chr5:1000-1000",
    "5:1000-1000",
    "chr5:1000",
    "chr5:1,000-1,000",
    "5:1,000-1,000",
    "chr5:1,000",

]


def test_regions_regex():
    for r in regions:
        assert '5:1000-1000' == RegionsMixin.get_region(r)


def test_get_regions_good():
    r = RegionsMixin.get_regions(regions=regions)
    assert r == [
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000'
    ]
