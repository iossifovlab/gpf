'''
Created on Nov 8, 2016

@author: lubo
'''
from __future__ import unicode_literals
from enrichment_tool.background import SynonymousBackground, \
    CodingLenBackground,\
    SamochaBackground
from precompute.register import Precompute


class SynonymousBackgroundPrecompute(SynonymousBackground, Precompute):

    def __init__(self):
        super(SynonymousBackgroundPrecompute, self).__init__(use_cache=True)

    def is_precomputed(self):
        return self.background is not None


class CodingLenBackgroundPrecompute(CodingLenBackground, Precompute):

    def __init__(self):
        super(CodingLenBackgroundPrecompute, self).__init__(use_cache=True)

    def is_precomputed(self):
        return self.background is not None


class SamochaBackgroundPrecompute(SamochaBackground, Precompute):

    def __init__(self):
        super(SamochaBackgroundPrecompute, self).__init__(use_cache=True)

    def is_precomputed(self):
        return self.background is not None
