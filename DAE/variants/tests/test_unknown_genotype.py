'''
Created on Feb 27, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
# import numpy as np


def test_query_regions(uagre):
    regions = [Region("1", 900719, 900719)]
    vs = uagre.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    for v in vl:
        print(v, v.alt)
        print(v.gt)
        print(v.best_st)
        assert v.best_st.shape == (2, 9)
#         assert np.all(np.sum(v.best_st, axis=0) == 2)
#         assert np.all(v.best_st >= 0)
