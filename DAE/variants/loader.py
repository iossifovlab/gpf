'''
Created on Feb 7, 2018

@author: lubo
'''
from pprint import pprint
import pandas as pd
import os


class StudyLoader(object):

    def __init__(self, study_config):
        self.config = study_config

    def load_summary(self):
        pprint(self.config)
        return True

    def load_pedigree(self):
        pprint(self.config)
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree)

        ped_df = pd.read_csv(self.config.pedigree, sep='\t', index_col=False)
        print(ped_df.head())
        ped = {}
        for p in ped_df.to_dict(orient='records'):
            ped[p['personId']] = p
        pprint(ped)

        assert len(ped) == len(ped_df)

        return ped_df
