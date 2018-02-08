'''
Created on Feb 7, 2018

@author: lubo
'''
import gzip
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd


class VCFWrapper(object):

    def __init__(self, filename):
        self.vcf_file = filename
        self.vcf = VCF(filename)
        self._samples = None

    @property
    def samples(self):
        if self._samples is None:
            self._samples = np.array(self.vcf.samples)
        return self._samples


class StudyLoader(object):

    def __init__(self, study_config):
        self.config = study_config

    def load_summary(self):
        print(self.config.summary)
        assert self.config.summary
        assert os.path.exists(self.config.summary)

        with gzip.GzipFile(self.config.summary, 'r') as infile:
            sum_df = pd.read_csv(infile, sep='\t', index_col=False)
        sum_df.drop('familyData', axis=1, inplace=True)
        print(sum_df.head())
        return sum_df

    def load_pedigree(self):
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree)

        ped_df = pd.read_csv(self.config.pedigree, sep='\t', index_col=False)
        ped = {}
        for p in ped_df.to_dict(orient='records'):
            ped[p['personId']] = p

        assert len(ped) == len(ped_df)

        return ped_df, ped

    def load_vcf(self):
        assert self.config.vcf
        assert os.path.exists(self.config.vcf)

        return VCFWrapper(self.config.vcf)
