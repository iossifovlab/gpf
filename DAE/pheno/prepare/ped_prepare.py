'''
Created on Jul 25, 2017

@author: lubo
'''
import numpy as np
import pandas as pd
from pheno.db import DbManager
from pheno.common import RoleMapping, Role, Status, Gender


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

    def _map_role_column(self, ped_df):
        mapping_name = self.config.person.role.mapping
        mapping = getattr(RoleMapping(), mapping_name)
        roles = pd.Series(ped_df.index)
        for index, row in ped_df.iterrows():
            role = mapping.get(row['role'])
            roles[index] = role.value
        ped_df['role'] = roles
        print(ped_df.head())
        return ped_df

    def _prepare_persons(self, ped_df):
        if self.config.person.role.type == 'column':
            ped_df = self._map_role_column(ped_df)
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

    @staticmethod
    def _build_sample_id(sample_id):
        if isinstance(sample_id, float) and np.isnan(sample_id):
            return None
        elif sample_id is None:
            return None

        return str(sample_id)

    def _save_persons(self, ped_df):
        families = self.db.get_families()
        persons = []
        for _index, row in ped_df.iterrows():
            p = {
                'family_id': families[row['familyId']].id,
                'person_id': row['personId'],
                'role': Role(row['role']),
                'status': Status(row['status']),
                'gender': Gender(row['gender']),
                'sample_id': self._build_sample_id(row['sampleId']),
            }
            persons.append(p)
        ins = self.db.person.insert()
        with self.db.engine.connect() as connection:
            connection.execute(ins, persons)

    def save(self, ped_df):
        self._save_families(ped_df)
        self._save_persons(ped_df)
