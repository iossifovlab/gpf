'''
Created on Feb 8, 2018

@author: lubo
'''
from variants.loader import StudyLoader, VariantMatcher
import numpy as np


class Study(object):

    def __init__(self, config):
        self.config = config

    def load(self):
        loader = StudyLoader(self.config)
        self.ped_df, self.ped = loader.load_pedigree()
        self.vcf = loader.load_vcf()
        self.samples = self.vcf.samples

        assert np.all(self.samples == self.ped_df['personId'].values)
        matcher = VariantMatcher(self.config)
        matcher.match()
        self.vars_df = matcher.vars_df
        self.vcf_vars = matcher.vcf_vars
        assert len(self.vars_df) == len(self.vcf_vars)

    def query_variants(self, **kwargs):
        pass
