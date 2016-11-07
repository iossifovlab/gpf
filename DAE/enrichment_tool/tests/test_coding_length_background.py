'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np

from enrichment_tool.background import CodingLenBackground


def test_coding_length_background_default():
    background = CodingLenBackground()
    background.precompute()

    assert background.background is not None

    background.cache_save()

    b1 = CodingLenBackground()
    assert b1.cache_load()
    assert b1.background is not None

    assert np.all(background.background == b1.background)
