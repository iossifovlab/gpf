'''
Created on Sep 10, 2016

@author: lubo
'''
import numpy as np
from collections import defaultdict, OrderedDict

from pheno.utils.configuration import PhenoConfig
from pheno.models import PersonManager, VariableManager, \
    ContinuousValueManager,\
    OrdinalValueManager, CategoricalValueManager, RawValueManager,\
    MetaVariableManager
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
        self.measure_name = name

    def __repr__(self):
        return "Measure({}, {}, {})".format(
            self.measure_id, self.type, self.value_domain.encode('utf-8'))

    @classmethod
    def from_df(cls, row):
        assert row['stats'] is not None

        m = Measure(row['measure_name'])
        m.measure_id = row['measure_id']
        m.instrument_name = row['instrument_name']
        m.type = row['stats']
        m.stats = row['stats']
        m.description = row['description']
        m.min_value = None
        m.max_value = None
        if m.stats == 'continuous' or m.stats == 'ordinal':
            m.min_value = row['min_value']
            m.max_value = row['max_value']
            assert m.max_value >= m.min_value
        m.value_domain = row['value_domain']

        return m


class MeasureMeta(Measure):

    def __init__(self, name):
        super(MeasureMeta, self).__init__(name)


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

    @staticmethod
    def _rename_forward(df, mapping):
        names = df.columns.tolist()
        for n, f in mapping:
            if n in names:
                names[names.index(n)] = f
        df.columns = names

    def _load_measures_meta_df(self, df):
        variable_ids = df.measure_id.unique()
        with MetaVariableManager() as vm:
            df = vm.load_df(where='variable_id IN ({})'.format(
                ','.join(["'{}'".format(v) for v in variable_ids])))

            print(df.head())

    def get_measures_df(self, instrument=None, stats=None, **kwmeta):
        assert instrument is None or instrument in self.instruments
        assert stats is None or \
            stats in set(['continuous', 'ordinal', 'categorical'])

        clauses = ["not stats isnull"]
        if instrument is not None:
            clauses.append("table_name = '{}'".format(instrument))
        if stats is not None:
            clauses.append("stats='{}'".format(stats))

        with VariableManager() as vm:
            df = vm.load_df(
                where=' and '.join(['( {} )'.format(c) for c in clauses]))

        res_df = df[[
            'variable_id', 'variable_name', 'table_name',
            'description', 'individuals', 'stats',
            'min_value', 'max_value', 'value_domain'
        ]]
        mapping = [
            ('variable_id', 'measure_id'),
            ('variable_name', 'measure_name'),
            ('table_name', 'instrument_name'),
        ]
        self._rename_forward(res_df, mapping)

        print(kwmeta)
        if kwmeta:
            print("joining meta...")
            meta_df = self._load_measures_meta_df(res_df)

        return res_df

    def get_measures(self, instrument=None, stats=None):
        df = self.get_measures_df(instrument, stats)
        res = OrderedDict()
        for _index, row in df.iterrows():
            m = Measure.from_df(row)
            res[m.measure_id] = m
        return res

    def _load_instruments(self):
        instruments = OrderedDict()

        df = self.get_measures_df()
        instrument_names = df.instrument_name.unique()

        for instrument_name in instrument_names:
            instrument = Instrument(instrument_name)
            measures = OrderedDict()
            measures_df = df[df.instrument_name == instrument_name]
            for _index, row in measures_df.iterrows():
                m = Measure.from_df(row)
                m.instrument = instrument
                measures[m.name] = m
            instrument.measures = measures
            instruments[instrument.name] = instrument

        self.instruments = instruments

    def _load_families(self):
        families = defaultdict(list)
        persons = self.get_persons()

        for p in persons.values():
            families[p.atts['family_id']].append(p)

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

    def get_persons_df(self, role=None):
        where = ["ssc_present=1"]
        if role:
            where.append("role='{}'".format(role))
        with PersonManager() as pm:
            df = pm.load_df(where=' and '.join(where))
            try:
                df.sort_values(['family_id', 'role_order'], inplace=True)
            except AttributeError:
                df = df.sort(['family_id', 'role_order'])

        return df[['person_id', 'family_id', 'role', 'gender']]

    def get_persons(self, role=None):
        persons = OrderedDict()
        df = self.get_persons_df(role)

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
        return persons

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

    def get_measure_values(self, measure_id, person_ids=None, role=None):
        df = self.get_measure_values_df(measure_id, person_ids, role)
        res = {}
        for _index, row in df.iterrows():
            res[row['person_id']] = row[measure_id]
        return res

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

    def get_persons_values_df(self, measure_ids, person_ids=None, role=None):
        persons_df = self.get_persons_df(role=role)

        value_df = self.get_values_df(
            measure_ids,
            role=role)

        df = persons_df.join(
            value_df.set_index('person_id'), on='person_id', rsuffix='_val')
        res_df = df.dropna()

        return res_df

    def _values_df_to_dict(self, measure_ids, df):
        res = {}
        for _index, row in df.iterrows():
            person_id = row.person_id
            vals = {}
            for mid in measure_ids:
                vals[mid] = row[mid]

            res[person_id] = vals

        return res

    def get_values(self, measure_ids, person_ids=None, role=None):
        df = self.get_values_df(measure_ids, person_ids, role)
        return self._values_df_to_dict(measure_ids, df)

    def get_instrument_measures(self, instrument_id):
        assert instrument_id in self.instruments
        measure_ids = [m.measure_id for
                       m in self.instruments[instrument_id].measures.values()]
        return measure_ids

    def get_instrument_values_df(
            self, instrument_id, person_ids=None, role=None):
        measure_ids = self.get_instrument_measures(instrument_id)
        res = self.get_values_df(measure_ids, person_ids, role)
        return res

    def get_instrument_values(
            self, instrument_id, person_ids=None, role=None):
        measure_ids = self.get_instrument_measures(instrument_id)
        df = self.get_values_df(measure_ids, person_ids, role)
        return self._values_df_to_dict(measure_ids, df)

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
        with VariableManager() as vm:
            variable = vm.get(
                where="variable_id='{}' and not stats isnull"
                .format(measure_id))
        return variable is not None
