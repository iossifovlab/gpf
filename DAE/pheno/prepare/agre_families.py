'''
Created on Nov 29, 2016

@author: lubo
'''
from pheno.utils.configuration import PhenoConfig
import os

import pandas as pd
import numpy as np


class AgreLoader(PhenoConfig):

    INDIVIDUALS = 'AGRE_Pedigree_Catalog_10-05-2012.csv'

    def __init__(self, *args, **kwargs):
        super(AgreLoader, self).__init__(*args, **kwargs)

    def load_table(self, table_name, roles=['prb'], dtype=None):
        result = []
        for data_dir in self._data_dirs(roles):
            dirname = os.path.join(self['agre', 'dir'], data_dir)
            assert os.path.isdir(dirname)

            filename = os.path.join(dirname, "{}.csv".format(table_name))
            if not os.path.isfile(filename):
                print("skipping {}...".format(filename))
                continue

            print("processing table: {}".format(filename))

            df = pd.read_csv(filename, low_memory=False, dtype=dtype)
            result.append(df)

        return result

    def _load_df(self, name, sep='\t', dtype=None):
        filename = os.path.join(self['agre', 'dir'], name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, sep=sep, dtype=dtype)

        return df

    def load_individuals(self):
        df = self._load_df(self.INDIVIDUALS)
        return df


class PrepareIndividuals(AgreLoader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividuals, self).__init__(*args, **kwargs)

    def _build_df_from_individuals(self):
        individuals = self.load_individuals()
        dtype = self._build_individuals_dtype()

        values = []
        for _index, row in individuals.iterrows():
            t = self._build_individuals_row(row)
            values.append(t)

        persons = np.array(values, dtype)
        persons = np.sort(persons, order=['familyId', 'roleOrder'])
        df = pd.DataFrame(persons)

        return df

    def _build_individuals_dtype(self):
        dtype = [('personId', 'S16'), ('familyId', 'S16'),
                 ('roleId', 'S8'), ('role', 'S8'),
                 ('roleOrder', int), ]
        return dtype

    def _build_role(self, row):
        if row['Person'] == 1:
            role = 'mo'
            role_type = 'mom'
            assert row['Sex'] == 'Female'
        elif row['Person'] == 2:
            role = 'fa'
            role_type = 'dad'
            assert row['Sex'] == 'Male'
        elif row['Scored Affected Status'] != '':
            role = 'p'
            role_type = 'prb'
        else:
            role = 's'
            role_type = 'sib'
        return role, role_type

    def _build_individuals_row(self, row):
        print(row)
        person_id = row['Individual Code']
        family_id = row['AU']
        role_id, role_type = self._build_role(row)
        role_order = row['Person']

        t = [person_id, family_id, role_id,
             role_type, role_order, ]
        return tuple(t)
