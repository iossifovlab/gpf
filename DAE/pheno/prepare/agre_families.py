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

    class Family(object):

        def __init__(self):
            self.family_id = None
            self.members = None

    class Individual(object):

        def __init__(self, row):
            self.au = row['AU']
            self.person = row['Person']
            self.father = row['Father']
            self.mother = row['Mother']
            self.individual_code = row['Individual Code']
            self.person_id = self.individual_code
            self.gender = self._build_gender(row['Sex'])
            self.role = self._build_role(row['Scored Affected Status'])

            self.key = (self.au, self.person)

        @staticmethod
        def _build_gender(sex):
            if sex.lower() == 'male':
                return 'M'
            elif sex.lower() == 'female':
                return 'F'
            else:
                raise ValueError("unexpected value for gender: {}"
                                 .format(sex))

        @staticmethod
        def _build_role(status):
            if status == 'Autism' or \
                    status == 'BroadSpectrum' or \
                    status == 'NQA' or \
                    status == 'ASD'or \
                    status == 'PDD-NOS':
                return 'prb'
            elif isinstance(status, float) and np.isnan(status):
                return 'sib'
            elif status == 'Not Met':
                return 'sib'
            else:
                print(type(status))
                raise ValueError("unexpected value for role: {}"
                                 .format(status))

    def __init__(self, *args, **kwargs):
        super(PrepareIndividuals, self).__init__(*args, **kwargs)

    def _build_individual(self, row):
        return PrepareIndividuals.Individual(row)

    def _build_individuals_df(self):
        df = self.load_individuals()
        individuals = self._build_individuals_dict(df)
        assert individuals is not None

        return 1

    def _build_individuals_dict(self, df):

        individuals = {}
        for _index, row in df.iterrows():
            individual = self._build_individual(row)
            individuals[individual.key] = individual

        return individuals

    def _build_families_dict(self, individuals):
        pass

#     def _build_df_from_individuals(self):
#         individuals = self.load_individuals()
#         dtype = self._build_individuals_dtype()
#
#         values = []
#         for _index, row in individuals.iterrows():
#             t = self._build_individuals_row(row)
#             values.append(t)
#
#         persons = np.array(values, dtype)
#         persons = np.sort(persons, order=['familyId', 'roleOrder'])
#         df = pd.DataFrame(persons)
#
#         return df

#     def _build_individuals_dtype(self):
#         dtype = [('personId', 'S16'), ('familyId', 'S16'),
#                  ('roleId', 'S8'), ('role', 'S8'),
#                  ('roleOrder', int), ]
#         return dtype
#
#     def _build_role(self, row):
#         if row['Person'] == 1:
#             role = 'mo'
#             role_type = 'mom'
#             assert row['Sex'] == 'Female'
#         elif row['Person'] == 2:
#             role = 'fa'
#             role_type = 'dad'
#             assert row['Sex'] == 'Male'
#         elif row['Scored Affected Status'] != '':
#             role = 'p'
#             role_type = 'prb'
#         else:
#             role = 's'
#             role_type = 'sib'
#         return role, role_type
#
#     def _build_individuals_row(self, row):
#         print(row)
#         person_id = row['Individual Code']
#         family_id = row['AU']
#         role_id, role_type = self._build_role(row)
#         role_order = row['Person']
#
#         t = [person_id, family_id, role_id,
#              role_type, role_order, ]
#         return tuple(t)
