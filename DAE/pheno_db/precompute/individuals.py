'''
Created on Aug 23, 2016

@author: lubo
'''
import os
import csv
import numpy as np
import pandas as pd

from pheno_db.utils.load_raw import V15Loader


class PrepareIndividuals(V15Loader):

    def __init__(self):
        super(PrepareIndividuals, self).__init__()

    @staticmethod
    def _role_order(role):
        if role == 'mo':
            return 0
        elif role == 'fa':
            return 10
        elif role[0] == 'p':
            return 20 + int(role[1])
        elif role[0] == 's':
            return 30 + int(role[1])
        else:
            raise ValueError("unexpected role: {}".format(role))

    @staticmethod
    def _role_type(role):
        if role == 'mo':
            return 'mom'
        elif role == 'fa':
            return 'dad'
        elif role[0] == 'p':
            return 'prb'
        elif role[0] == 's':
            return 'sib'

    def _build_df_from_individuals(self):
        individuals = self.load_individuals()
        v15_index = individuals['Version 15: 2013-08-06'] == 1
        v15 = individuals[v15_index]

        dtype = [
            ('person_id', 'S16'), ('family_id', 'S16'),
            ('role_id', 'S8'), ('role', 'S8'),
            ('role_order', int), ('collection', 'S64')
        ]
        values = []
        for _index, row in v15.iterrows():
            person_id = row['SSC ID']
            collection = row['Collection']
            [family_id, role_id] = person_id.split('.')
            role_order = PrepareIndividuals._role_order(role_id)
            role_type = PrepareIndividuals._role_type(role_id)
            values.append(
                (person_id, family_id, role_id,
                 role_type, role_order, collection))

        persons = np.array(values, dtype)
        persons = np.sort(persons, order=['family_id', 'role_order'])
        df = pd.DataFrame(persons)
        return df

    def cache(self, df):
        cache_dir = self.cache_dir
        filename = os.path.join(cache_dir, 'individuals.csv')

        df.to_csv(filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)

    def prepare(self):
        df = self._build_df_from_individuals()
        return df


def prepare_individuals():
    loader = V15Loader()
    individuals = loader.load_individuals()

    return individuals
