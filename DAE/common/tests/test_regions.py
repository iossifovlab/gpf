'''
Created on Feb 20, 2017

@author: lubo
'''
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
    mixin = RegionsMixin()
    for r in regions:
        m = mixin.REGION_REGEXP2.match(r)
        print(r, m.groups())
        print(r, RegionsMixin.get_region(r))
        assert '5:1000-1000' == RegionsMixin.get_region(r)


def test_get_regions_good():
    r = RegionsMixin.get_regions(regions=regions)
    print(r)
    assert r == [
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000',
        '5:1000-1000'
    ]
