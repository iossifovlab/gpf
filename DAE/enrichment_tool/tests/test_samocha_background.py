'''
Created on Nov 7, 2016

@author: lubo
'''
from enrichment_tool.background import SamochaBackground


def test_samocha_background_default():
    background = SamochaBackground()
    background.precompute()

    assert background.background is not None
