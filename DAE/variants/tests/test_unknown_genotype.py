'''
Created on Feb 27, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
from variants.attributes import Inheritance


def test_query_regions(ustudy_vcf):
    regions = [Region("1", 900719, 900719)]
    vs = ustudy_vcf.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    v = vl[0]

    print(v, v.alts)
    print(v.gt)
    print(v.best_st)

    assert v.inheritance == Inheritance.unknown

    assert v.best_st.shape == (2, 9)
    assert v.best_st[0, 0] == -1
    assert v.best_st[1, 0] == -1
    assert v.best_st[0, 6] == -1
    assert v.best_st[1, 6] == -1
