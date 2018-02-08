'''
Created on Feb 8, 2018

@author: lubo
'''
from variants.loader import StudyLoader
import numpy as np


class Study(object):

    def __init__(self, config):
        self.config = config

    def load(self):
        loader = StudyLoader(self.config)
        self.ped_df, self.ped = loader.load_pedigree()
        vcf = loader.load_vcf()
        self.samples = vcf.samples

        assert np.all(self.samples == self.ped_df['personId'].values)

    def query_variants(self, **kwargs):
        pass
