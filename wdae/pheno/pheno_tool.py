'''
Created on Aug 9, 2016

@author: lubo
'''
import copy
from collections import Counter
from query_variants import dae_query_families_with_variants


class PhenoTool(object):

    def __init__(self, req):
        self.req = req
        self.effect_type_groups = req.effect_type_groups
        self.data = req.data

    def build_families_with_variants(self):
        result = {}
        for effect_type in self.effect_type_groups:
            data = copy.deepcopy(self.data)
            data['effectTypes'] = effect_type
            data['inChild'] = 'prb'

            fams = dae_query_families_with_variants(data)
            result[effect_type] = Counter(fams)

        return result
