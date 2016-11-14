'''
Created on Nov 8, 2016

@author: lubo
'''
from enrichment_tool.background import SynonymousBackground, \
    CodingLenBackground,\
    SamochaBackground
from precompute.register import Precompute


class SynonymousBackgroundPrecompute(SynonymousBackground, Precompute):

    def __init__(self):
        super(SynonymousBackgroundPrecompute, self).__init__(use_cache=True)


class CodingLenBackgroundPrecompute(CodingLenBackground, Precompute):

    def __init__(self):
        super(CodingLenBackgroundPrecompute, self).__init__(use_cache=True)


class SamochaBackgroundPrecompute(SamochaBackground, Precompute):

    def __init__(self):
        super(SamochaBackgroundPrecompute, self).__init__(use_cache=True)
