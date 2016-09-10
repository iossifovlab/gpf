'''
Created on Sep 10, 2016

@author: lubo
'''


from pheno.utils.configuration import PhenoConfig
from pheno.models import PersonManager


class PhenoDB(PhenoConfig):

    def __init__(self, dae_config=None, *args, **kwargs):
        super(PhenoDB, self).__init__(dae_config, *args, **kwargs)

        self.families = None
        self.instruments = None

    def _load_families(self):
        with PersonManager(config=self.config) as pm:
            df = pm.load_df(where="ssc_present=1")
            print(len(df))
            print(df.columns)
            print(df.head())

    def load(self):
        self._load_families()
