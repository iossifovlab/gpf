'''
Created on Aug 25, 2016

@author: lubo
'''
import numpy as np
import pandas as pd
from pheno.models import PersonManager, PersonModel
from pheno.utils.load_raw import V15Loader


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

    def _build_individuals_dtype(self):
        dtype = [('personId', 'S16'), ('familyId', 'S16'),
                 ('roleId', 'S8'), ('role', 'S8'),
                 ('roleOrder', int), ('collection', 'S64')]
        return dtype

    def _build_individuals_row(self, row):
        person_id = row['SSC ID']
        collection = row['Collection']
        [family_id, role_id] = person_id.split('.')
        role_order = self._role_order(role_id)
        role_type = self._role_type(role_id)
        t = [person_id, family_id, role_id,
             role_type, role_order, collection]
        return tuple(t)

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

    def prepare(self):
        df = self._build_df_from_individuals()

        manager = PersonManager()
        manager.delete()
        manager.create_tables()

        manager.connect()
        assert manager.db is not None

        for _index, row in df.iterrows():
            p = PersonModel()
            p.person_id = row['personId']
            p.family_id = row['familyId']
            p.role = row['role']
            p.role_id = row['roleId']
            p.gender = None
            p.race = None
            p.collection = None if (isinstance(row['collection'], float) or
                                    row['collection'] == 'nan') \
                else row['collection']
            p.ssc_present = None

            manager.save(p)

        manager.close()


class PrepareIndividualsGender(V15Loader):

    def __init__(self):
        super(PrepareIndividualsGender, self).__init__()

    def _build_proband_gender(self, df):
        [cd] = self.load_table('ssc_core_descriptive', roles=['prb'])
        for _index, row in cd.iterrows():
            pid = row['individual']
            gender = row['sex'].upper()[0]
            df.loc[df.person_id == pid, 'gender'] = gender
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
                df.loc[df.person_id == pid, 'gender'] = gender
        return df

    def _build_gender(self, df):
        gender = df['gender']

        gender[df.role == 'mom'] = 'F'
        gender[df.role == 'dad'] = 'M'

        df = self._build_proband_gender(df)
        df = self._build_siblings_gender(df)

        return df

    def prepare(self):
        pm = PersonManager()
        pm.connect()
        df = pm.load_df()

        self._build_gender(df)

        manager = PersonManager()
        manager.connect()

        for _index, row in df.iterrows():
            p = PersonModel.create_from_df(row)
            manager.save(p)

        manager.close()
