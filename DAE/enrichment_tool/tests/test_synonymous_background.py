'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np

from enrichment_tool.background import SynonymousBackground


def test_synonymous_background_default():
    background = SynonymousBackground()
    background.precompute()

    assert background.background is not None
    assert background.foreground is not None

    background.cache_save()

    b1 = SynonymousBackground()
    assert b1.cache_load()
    assert b1.background is not None
    assert b1.foreground is not None

    assert np.all(background.background == b1.background)
    assert np.all(background.foreground == b1.foreground)


def test_cache_clear():
    background = SynonymousBackground()
    background.cache_clear()
    background.cache_clear()

    assert not background.cache_load()
