'''
Created on Feb 23, 2018

@author: lubo
'''
from RegionOperations import Region
import numpy as np


def test_query_regions(ustudy):
    regions = [Region("1", 900717, 900717)]
    vs = ustudy.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    for v in vl:
        print(v)
        print(v.gt)
        print(v.best_st)
        assert v.best_st.shape == (3, 9)
        assert np.all(np.sum(v.best_st, axis=0) == 2)
        assert np.all(v.best_st >= 0)
