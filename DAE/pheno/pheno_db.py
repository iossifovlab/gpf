'''
Created on Sep 10, 2016

@author: lubo
'''
import numpy as np
from collections import defaultdict, OrderedDict

from pheno.utils.configuration import PhenoConfig
from pheno.models import PersonManager, VariableManager
from VariantsDB import Person, Family


class Instrument(object):

    def __init__(self, name):
        self.name = name

        self.measures = OrderedDict()

    def __repr__(self):
        return "Instrument({}, {})".format(self.name, len(self.measures))


class Measure(object):

    def __init__(self, name):
        self.name = name
        self.instrument = None

    def __repr__(self):
        return "Measure({}, {}, {})".format(
            self.measure_id, self.type, self.value_domain.encode('utf-8'))

    @staticmethod
    def from_df(row):
        assert row['stats'] is not None

        m = Measure(row['variable_name'])
        m.measure_id = row['variable_id']
        m.instrument_name = row['table_name']
        m.type = row['stats']
        m.stats = row['stats']
        m.description = row['description']
        m.min_value = None
        m.max_value = None
        if m.type == 'continuous' or m.type == 'ordinal':
            m.min_value = row['min_value']
            m.max_value = row['max_value']
            assert m.max_value >= m.min_value
        m.value_domain = row['value_domain']

        return m


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

    def _load_instruments(self):
        instruments = OrderedDict()
        with VariableManager(config=self.config) as vm:
            df = vm.load_df(where="not (stats isnull)")
            table_names = df.table_name.unique()

            for table_name in table_names:
                instrument = Instrument(table_name)
                measures = OrderedDict()
                measures_df = df[df.table_name == table_name]
                for _index, row in measures_df.iterrows():
                    m = Measure.from_df(row)
                    m.instrument = instrument
                    measures[m.name] = m
                instrument.measures = measures
                instruments[instrument.name] = instrument

        self.instruments = instruments

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
        self._load_instruments()
