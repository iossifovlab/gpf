'''
Created on Jul 25, 2017

@author: lubo
'''
import numpy as np
import pandas as pd
from pheno.db import DbManager
from pheno.common import RoleMapping, Role, Status, Gender, MeasureType
import os
import math
from box import Box


class PrepareBase(object):
    PID_COLUMN = "$PID"
    PERSON_ID = 'person_id'

    def __init__(self, config):
        assert config is not None
        self.config = config
        self.db = DbManager(self.config.db.filename)
        self.db.build()
        self.persons = None

    def get_persons(self, force=False):
        if not self.persons or force:
            self.persons = self.db.get_persons()
        return self.persons


class PreparePersons(PrepareBase):
    COLUMNS = [
        'familyId', 'personId', 'dadId', 'momId',
        'gender', 'status', 'sampleId'
    ]

    def __init__(self, config):
        super(PreparePersons, self).__init__(config)

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
        return ped_df

    def _prepare_persons(self, ped_df):
        if self.config.person.role.type == 'column':
            ped_df = self._map_role_column(ped_df)
        return ped_df

    @classmethod
    def load_pedfile(cls, pedfile):
        df = pd.read_csv(pedfile, sep='\t')
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
                self.PERSON_ID: row['personId'],
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


class PrepareVariables(PrepareBase):

    def __init__(self, config):
        super(PrepareVariables, self).__init__(config)

    def load_instrument(self, filenames):
        assert filenames
        assert all([os.path.exists(f) for f in filenames])

        instrument_names = [
            os.path.splitext(os.path.basename(f))[0]
            for f in filenames
        ]
        assert len(set(instrument_names)) == 1

        dataframes = []
        for filename in filenames:
            df = pd.read_csv(filename, sep=',')
            person_id = df.columns[0]
            df.rename(columns={person_id: self.PERSON_ID}, inplace=True)
            dataframes.append(df)
        assert len(dataframes) >= 1

        if len(dataframes) == 1:
            df = dataframes[0]
        else:
            df = None
        assert df is not None

        persons = self.get_persons()
        assert set(df.person_id.unique()) <= set(persons.keys())

        pid = pd.Series(df.index)
        for index, row in df.iterrows():
            p = persons[row[self.PERSON_ID]]
            assert p is not None
            assert p.person_id == row[self.PERSON_ID]
            pid[index] = p.id
        df[self.PID_COLUMN] = pid

        instrument_name = instrument_names[0]
        df = self._adjust_instrument_measure_names(instrument_name, df)
        return instrument_name, df

    def _adjust_instrument_measure_names(self, instrument_name, df):
        columns = {}
        for index in range(1, len(df.columns)):
            name = df.columns[index]
            parts = [p.strip() for p in name.split('.')]
            parts = [p for p in parts if p != instrument_name]
            columns[name] = '.'.join(parts)
        df.rename(columns=columns, inplace=True)
        return df

    def _save_measure(self, measure, mdf):
        to_save = measure.to_dict()
        ins = self.db.measure.insert().values(**to_save)
        with self.db.engine.connect() as connection:
            result = connection.execute(ins)
            measure_id = result.inserted_primary_key[0]
        values = []
        for _index, row in mdf.iterrows():
            v = {
                self.PERSON_ID: row[self.PID_COLUMN],
                'measure_id': measure_id,
                'value': row['value']
            }
            values.append(v)
        value_table = self.db.get_value_table(measure.measure_type)
        ins = value_table.insert()
        with self.db.engine.connect() as connection:
            connection.execute(ins, values)

    def prepare_instrument(self, filenames):
        instrument_name, df = self.load_instrument(filenames)
        assert instrument_name is not None
        assert df is not None
        assert self.PERSON_ID in df.columns

        for measure_name in df.columns[1:]:
            if measure_name in self.config.skip.measures or \
                    measure_name == self.PID_COLUMN:
                continue
            mdf = df[[self.PERSON_ID, self.PID_COLUMN, measure_name]].dropna()
            mdf.rename(columns={measure_name: 'value'}, inplace=True)

            measure = self._build_measure(instrument_name, measure_name, mdf)
            self._save_measure(measure, mdf)
        return df

    @classmethod
    def check_values_type(cls, values):
        boolean = all([isinstance(v, bool) for v in values])
        if boolean:
            return bool

        try:
            vals = [v.strip() for v in values]
            fvals = [float(v) for v in vals if v != '']
        except ValueError:
            return str

        hvals = [math.floor(v) for v in fvals]
        lvals = [math.ceil(v) for v in fvals]

        check_float = [v1 == v2 for (v1, v2) in zip(hvals, lvals)]
        if all(check_float):
            return int
        else:
            return float

    def check_continuous_rank(self, rank, individuals):
        if rank < self.config.classification.continuous.min_rank:
            return False
        if individuals < self.config.classification.min_individuals:
            return False
        return True

    def check_ordinal_rank(self, rank, individuals):
        if rank < self.config.classification.ordinal.min_rank:
            return False
        if individuals < self.config.classification.min_individuals:
            return False
        return True

    def check_categorical_rank(self, rank, individuals):
        if rank < self.config.classification.categorical.min_rank:
            return False
        if individuals < self.config.classification.min_individuals:
            return False
        return True

    DOMAIN_MAX_DISPLAY = 5

    def _value_domain_list(self, unique_values):
        unique_values = sorted(unique_values)
        unique_values = [str(v) for v in unique_values]
        if len(unique_values) >= self.DOMAIN_MAX_DISPLAY:
            unique_values = unique_values[:self.DOMAIN_MAX_DISPLAY + 1]
            unique_values[self.DOMAIN_MAX_DISPLAY] = '...'
        return "{}".format(','.join([v for v in unique_values]))

    def _default_measure(self, instrument_name, measure_name):
        measure = {'measure_type': MeasureType.other,
                   'measure_name': measure_name,
                   'instrument_name': instrument_name,
                   'measure_id': '{}.{}'.format(instrument_name, measure_name),
                   'min_value': None,
                   'max_value': None,
                   'value_domain': None,
                   'individuals': None,
                   'default_filter': None}
        measure = Box(measure)
        return measure

    def _build_measure(self, instrument_name, measure_name, df):
        measure = self._default_measure(instrument_name, measure_name)

        values = df['value']
        unique_values = values.unique()
        rank = len(unique_values)
        individuals = len(df)
        measure.individuals = individuals

        if individuals == 0:
            return measure

        values_type = values.dtype
        if values_type == np.object:
            values_type = self.check_values_type(unique_values)

        if values_type in set([str, bool, np.bool, np.dtype('bool')]):
            if self.check_categorical_rank(rank, individuals):
                measure.measure_type = MeasureType.categorical
                measure.value_domain = self._value_domain_list(unique_values)
                return measure
        elif values_type in set([int, float, np.float, np.int,
                                 np.dtype('int64'), np.dtype('float64')]):
            measure.min_value = values.min()
            measure.max_value = values.max()
            if self.check_continuous_rank(rank, individuals):
                measure.measure_type = MeasureType.continuous
                measure.value_domain = '[{},{}]'.format(
                    measure.min_value,
                    measure.max_value
                )
                return measure
            if self.check_ordinal_rank(rank, individuals):
                measure.measure_type = MeasureType.continuous
                unique_values = sorted(unique_values)
                measure.value_domain = "{}".format(
                    ', '.join([str(v) for v in unique_values]))
                return measure
            if self.check_categorical_rank(rank, individuals):
                measure.measure_type = MeasureType.categorical
                measure.value_domain = self._value_domain_list(unique_values)
                return measure
        else:
            measure.measure_type = MeasureType.other
            measure.value_domain = self._value_domain_list(unique_values)
            return measure
