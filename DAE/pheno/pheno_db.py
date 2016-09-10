'''
Created on Sep 10, 2016

@author: lubo
'''
import numpy as np
from collections import defaultdict

from pheno.utils.configuration import PhenoConfig
from pheno.models import PersonManager
from VariantsDB import Person, Family


class PhenoDB(PhenoConfig):

    def __init__(self, dae_config=None, *args, **kwargs):
        super(PhenoDB, self).__init__(dae_config, *args, **kwargs)

        self.families = None
        self.persons = None
        self.instruments = None

    @staticmethod
    def check_nan(val):
        if not isinstance(val, float):
            raise ValueError("unexpected value: {}".format(val))

        if np.isnan(val):
            return None
        else:
            return val

    def _load_families(self):
        persons = {}
        families = defaultdict(list)

        with PersonManager(config=self.config) as pm:
            df = pm.load_df(where="ssc_present=1")
            try:
                df.sort_values(['family_id', 'role_order'], inplace=True)
            except AttributeError:
                df = df.sort(['family_id', 'role_order'])

            for _index, row in df.iterrows():
                person_id = row['person_id']
                family_id = row['family_id']

                atts = {
                    'family_id': family_id,
                    'person_id': person_id,
                    'role': row['role'],
                    'gender': row['gender'],
                    'age': self.check_nan(row['age']),
                    'non_verbal_iq': self.check_nan(row['non_verbal_iq']),
                    'verbal_iq': self.check_nan(row['verbal_iq']),
                    'race': row['race'],
                }
                p = Person(atts)
                p.personId = person_id
                p.role = atts['role']
                p.gender = atts['gender']

                persons[person_id] = p
                families[family_id].append(p)

        self.persons = persons
        self.families = {}

        for family_id, members in families.items():
            f = Family()
            f.memberInOrder = members
            f.familyId = family_id
            self.families[family_id] = f

    def load(self):
        self._load_families()
