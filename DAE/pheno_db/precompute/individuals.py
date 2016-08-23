'''
Created on Aug 23, 2016

@author: lubo
'''
import os
import csv
import numpy as np
import pandas as pd

from pheno_db.utils.load_raw import V15Loader
from pheno_db.utils.configuration import PhenoConfig
from VariantsDB import Family, Person
from collections import defaultdict


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
        elif role[0] == 's' or role[0] == 'x':
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
        elif role[0] == 's' or role[0] == 'x':
            return 'sib'

    VERSION2LABEL = {
        'v1': 'Version 1:  2008-11-01',
        'v2': 'Version 2:  2009-02-01',
        'v3': 'Version 3:  2009-04-20',
        'v4': 'Version 4:  2009-05-01',
        'v5': 'Version 5:  2009-08-01',
        'v6': 'Version 6:  2009-11-01',
        'v7': 'Version 7:  2010-02-01',
        'v8': 'Version 8:  2010-05-02',
        'v9': 'Version 9:  2010-08-02',
        'v10': 'Version 10:  2010-11-01',
        'v11': 'Version 11: 2011-02-04',
        'v12': 'Version 12: 2011-05-02',
        'v13': 'Version 13: 2011-08-09',
        'v14': 'Version 14: 2011-08-09',
        'v15': 'Version 15: 2013-08-06',
    }
    VERSIONS = [
        'v1', 'v2', 'v3', 'v4', 'v5',
        'v6', 'v7', 'v8', 'v9',
        'v10', 'v11', 'v12', 'v13', 'v14', 'v15']

    def _build_individuals_dtype(self):
        dtype = [('personId', 'S16'), ('familyId', 'S16'),
                 ('roleId', 'S8'), ('role', 'S8'),
                 ('roleOrder', int), ('collection', 'S64'),
                 ('gender', 'S8')]
        for ver in self.VERSIONS:
            dtype.append((ver, int))

        return dtype

    def _build_individuals_versions_index(self, individuals):
        index = individuals[self.VERSION2LABEL[self.VERSIONS[0]]]

        for ver in self.VERSIONS[1:]:
            index = np.logical_or(index, individuals[self.VERSION2LABEL[ver]])
        return index

    def _build_individuals_row(self, row):
        person_id = row['SSC ID']
        collection = row['Collection']
        [family_id, role_id] = person_id.split('.')
        role_order = PrepareIndividuals._role_order(role_id)
        role_type = PrepareIndividuals._role_type(role_id)
        t = [person_id, family_id, role_id,
             role_type, role_order, collection,
             'X']
        for ver in self.VERSIONS:
            v = row[self.VERSION2LABEL[ver]]
            t.append(1 if v else 0)

        return tuple(t)

    def _build_df_from_individuals(self):
        individuals = self.load_individuals()
        index = self._build_individuals_versions_index(individuals)

        df = individuals[index]
        dtype = self._build_individuals_dtype()

        values = []
        for _index, row in df.iterrows():
            t = self._build_individuals_row(row)
            values.append(t)

        persons = np.array(values, dtype)
        persons = np.sort(persons, order=['familyId', 'roleOrder'])
        df = pd.DataFrame(persons)

        return df

    def cache(self, df):
        cache_dir = self.cache_dir
        filename = os.path.join(cache_dir, 'individuals.csv')

        df.to_csv(filename, index=False, sep=',', quoting=csv.QUOTE_NONNUMERIC)

    def prepare(self):
        df = self._build_df_from_individuals()
        df = self._build_gender(df)

        return df

    def _build_proband_gender(self, df):
        [cd] = self.load_table('ssc_core_descriptive', roles=['prb'])
        for _index, row in cd.iterrows():
            pid = row['individual']
            gender = row['sex'].upper()[0]
            df.loc[df.personId == pid, 'gender'] = gender
        return df

    def _build_siblings_gender(self, df):
        cds = self.load_table('ssc_core_descriptive', roles=['sib'])
        for cd in cds:
            for _index, row in cd.iterrows():
                pid = row['individual']
                if isinstance(row['sex'], float):
                    gender = 'X'
                else:
                    gender = row['sex'].upper()[0]
                df.loc[df.personId == pid, 'gender'] = gender
        return df

    def _build_gender(self, df):
        gender = pd.Series('X', df.index)

        gender[df.role == 'mom'] = 'F'
        gender[df.role == 'dad'] = 'M'

        df['gender'] = gender

        df = self._build_proband_gender(df)
        df = self._build_siblings_gender(df)

        return df


class Individuals(PhenoConfig):

    def __init__(self):
        super(Individuals, self).__init__()

    def load(self):
        cache_dir = self.cache_dir
        filename = os.path.join(cache_dir, 'individuals.csv')
        self.df = pd.read_csv(filename, dtype={
            'personId': 'S16', 'familyId': 'S16',
            'roleId': 'S8', 'role': 'S8', 'roleOrder': 'S8',
            'collection': 'S64', 'gender': 'S8'})

        self.families = defaultdict(Family)
        for _index, row in self.df.iterrows():

            family_id = row['familyId']
            self.families[family_id].familyId = family_id

            atts = {index: value for index, value in row.iteritems()}

            person = Person(atts)
            person.personId = atts['personId']
            person.role = atts['role']

            self.families[family_id].memberInOrder.append(person)
