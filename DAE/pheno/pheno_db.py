'''
Created on Sep 10, 2016

@author: lubo
'''
import numpy as np
from collections import defaultdict, OrderedDict

from pheno.utils.configuration import PhenoConfig
from pheno.models import PersonManager, VariableManager, \
    ContinuousValueManager,\
    OrdinalValueManager, CategoricalValueManager, RawValueManager
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

    def get_measure_type(self, measure_id):
        with VariableManager() as vm:
            variable = vm.get(
                where="variable_id='{}' and not stats isnull"
                .format(measure_id))
        if not variable:
            return None
        else:
            return variable.stats

    def _get_values_df(self, value_manager, where):
        with value_manager() as vm:
            df = vm.load_df(where=where)
            return df

        return None

    def _get_value_manager(self, value_type):
        if value_type == 'continuous':
            return ContinuousValueManager
        elif value_type == 'ordinal':
            return OrdinalValueManager
        elif value_type == 'categorical':
            return CategoricalValueManager
        else:
            raise ValueError("unsupported value type: {}".format(value_type))

    @staticmethod
    def _rename_value_column(measure_id, df):
        names = df.columns.tolist()
        names[names.index('value')] = measure_id
        df.columns = names

    def get_measure_values_df(self, measure_id, person_ids=None, role=None):
        assert measure_id is not None
        value_type = self.get_measure_type(measure_id)
        if value_type is None:
            raise ValueError("bad measure: {}; unknown value type"
                             .format(measure_id))
        value_manager = self._get_value_manager(value_type)

        clauses = ["variable_id = '{}'".format(measure_id)]
        if role:
            clauses.append("person_role = '{}'".format(role))
        where = ' and '.join(clauses)

        df = self._get_values_df(value_manager, where)
        if person_ids:
            df = df[df.person_id.isin(person_ids)]

        self._rename_value_column(measure_id, df)

        return df[['person_id', measure_id]]

    def get_values_df(self, measure_ids, person_ids=None, role=None):
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert all([self.has_measure(m) for m in measure_ids])

        dfs = [self.get_measure_values_df(m, person_ids, role)
               for m in measure_ids]

        res_df = dfs[0]
        for i, df in enumerate(dfs[1:]):
            res_df = res_df.join(
                df.set_index('person_id'), on='person_id',
                rsuffix='_val_{}'.format(i))

        return res_df

    def get_instrument_values(self, instrument_id, person_id):
        where = "person_id = '{}' and variable_id in " \
            "(select variable_id from variable where table_name='{}')" \
            .format(person_id, instrument_id)

        vms = [
            ContinuousValueManager,
            OrdinalValueManager,
            CategoricalValueManager,
        ]
        dfs = [self._get_values_df(vm, where) for vm in vms]

        def todict(df):
            res = {}
            for _index, row in df.iterrows():
                res[row['variable_id']] = row['value']
            return res

        res = {}
        [res.update(todict(df)) for df in dfs]

        return res

    def get_measure_values(self, measure_id, person_ids=None, role=None):
        df = self.get_measure_values_df(measure_id, person_ids, role)
        res = {}
        for _index, row in df.iterrows():
            res[row['person_id']] = row[measure_id]
        return res

    def get_instruments(self, person_id):
        query = "SELECT DISTINCT table_name FROM variable WHERE " \
            "variable_id IN " \
            "(SELECT variable_id FROM value_raw WHERE person_id='{}')" \
            .format(person_id)
        with RawValueManager() as vm:
            instruments = vm._execute(query)
        return dict([(i[0], self.instruments[i[0]]) for i in instruments
                     if i[0] in self.instruments])

    @staticmethod
    def split_measure_id(measure_id):
        if '.' not in measure_id:
            return (None, measure_id)
        else:
            [instrument_name, measure_name] = measure_id.split('.')
            return (instrument_name, measure_name)

    def has_measure(self, measure_id):
        if measure_id in set(['non_verbal_iq', 'verbal_iq']):
            return True
        with VariableManager() as vm:
            variable = vm.get(
                where="variable_id='{}' and not stats isnull"
                .format(measure_id))
        return variable is not None

    def _get_person_df(self, role):
        where = ["ssc_present=1"]
        if role:
            where.append("role='{}'".format(role))
        with PersonManager() as pm:
            persons_df = pm.load_df(where=' and '.join(where))
        return persons_df

    def get_measure_df(self, measure_id, role='prb'):
        if not self.has_measure(measure_id):
            raise ValueError("unsupported phenotype measure")

        persons_df = self._get_person_df(role)
        if measure_id in set(['non_verbal_iq', 'verbal_iq']):
            return persons_df

        value_df = self.get_values_df(measure_id, role=role)
        print(len(value_df))

        df = persons_df.join(
            value_df.set_index('person_id'), on='person_id', rsuffix='_val')

        _instrument, measure_name = self.split_measure_id(measure_id)

        names = df.columns.tolist()
        names[names.index('value')] = measure_name
        df.columns = names

        return df[['person_id', 'family_id', 'role',
                   'gender', 'race', 'age', 'non_verbal_iq',
                   measure_name]]
