'''
Created on Jul 25, 2017

@author: lubo
'''
import pandas as pd
from pheno.db import DbManager


class PreparePersons(object):
    COLUMNS = [
        'familyId', 'personId', 'dadId', 'momId',
        'gender', 'status', 'sampleId'
    ]

    def __init__(self, config):
        assert config is not None
        self.config = config
        self.db = DbManager(self.config.db.filename)
        self.db.build()

    def _prepare_families(self, ped_df):
        if self.config.family.composite_key:
            pass
        return ped_df

    def _prepare_persons(self, ped_df):
        return ped_df

    @classmethod
    def load_pedfile(cls, pedfile):
        df = pd.read_csv(pedfile, sep='\t')
        print(df.columns)
        assert set(cls.COLUMNS) <= set(df.columns)
        return df

    def prepare(self, ped_df):
        assert set(self.COLUMNS) <= set(ped_df.columns)
        ped_df = self._prepare_families(ped_df)
        ped_df = self._prepare_persons(ped_df)
        return ped_df

    def _save_families(self, ped_df):
        families = [
            {'family_id': fid} for fid in ped_df['familyId'].unique()
        ]
        ins = self.db.family.insert()
        with self.db.engine.connect() as connection:
            connection.execute(ins, families)

    def save(self, ped_df):
        self._save_families(ped_df)
