'''
Created on Jul 25, 2017

@author: lubo
'''
from __future__ import print_function
import numpy as np
import pandas as pd
from pheno.db import DbManager
from pheno.common import RoleMapping, Role, Status, Gender, MeasureType
import os
import math
from box import Box
from collections import defaultdict, OrderedDict
from pheno.utils.commons import remove_annoying_characters
from pheno.pheno_db import PhenoDB, Measure


class PrepareBase(object):
    PID_COLUMN = "$PID"
    PERSON_ID = 'person_id'

    PED_COLUMNS = [
        'familyId', 'personId', 'dadId', 'momId',
        'gender', 'status',
        # 'sampleId',
        # 'role',
    ]

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

    def __init__(self, config):
        super(PreparePersons, self).__init__(config)

    def _prepare_families(self, ped_df):
        if self.config.family.composite_key:
            pass
        return ped_df

    def _map_role_column(self, ped_df):
        assert self.config.person.role.type == 'column'
        role_column = self.config.person.role.column
        assert role_column in ped_df.columns, \
            "can't find column '{}' into pedigree file".format(role_column)
        mapping_name = self.config.person.role.mapping
        mapping = getattr(RoleMapping(), mapping_name)
        assert mapping is not None, \
            "bad role mapping '{}'".format(mapping_name)

        roles = pd.Series(ped_df.index)
        for index, row in ped_df.iterrows():
            role = mapping.get(row['role'])
            roles[index] = role.value
        ped_df['role'] = roles
        return ped_df

    @staticmethod
    def _find_parent_in_family_ped(family_df, mom_or_dad):
        df = family_df[family_df[mom_or_dad] != '0']
        assert len(df[mom_or_dad].unique()) <= 1
        if len(df) == 1:
            row = df.iloc[0]
            return (row.familyId, row.personId)
        return None

    @staticmethod
    def _find_mom_in_family_ped(family_df):
        return PreparePersons._find_parent_in_family_ped(family_df, 'momId')

    @staticmethod
    def _find_dad_in_family_ped(family_df):
        return PreparePersons._find_parent_in_family_ped(family_df, 'dadId')

    @staticmethod
    def _find_status_in_family(family_df, status):
        df = family_df[family_df.status == status]
        result = []
        for row in df.to_dict('records'):
            result.append((row['familyId'], row['personId']))
        return result

    @staticmethod
    def _find_prb_in_family(family_df):
        return PreparePersons._find_status_in_family(
            family_df, Status.affected.value)

    @staticmethod
    def _find_sib_in_family(family_df):
        return PreparePersons._find_status_in_family(
            family_df, Status.unaffected.value)

    def _guess_role_nuc(self, ped_df):
        assert self.config.person.role.type == 'guess'
        grouped = ped_df.groupby('familyId')
        roles = {}
        for _, family_df in grouped:
            mom = self._find_mom_in_family_ped(family_df)
            if mom:
                roles[mom] = Role.mom
            dad = self._find_dad_in_family_ped(family_df)
            if dad:
                roles[dad] = Role.dad
            for p in self._find_prb_in_family(family_df):
                roles[p] = Role.prb
            for p in self._find_sib_in_family(family_df):
                roles[p] = Role.sib
        assert len(roles) == len(ped_df)

        role = pd.Series(ped_df.index)
        for index, row in ped_df.iterrows():
            role[index] = roles[(row['familyId'], row['personId'])]
        ped_df['role'] = role
        return ped_df

    def _prepare_persons(self, ped_df):
        if self.config.person.role.type == 'column':
            ped_df = self._map_role_column(ped_df)
        elif self.config.person.role.type == 'guess':
            ped_df = self._guess_role_nuc(ped_df)
        return ped_df

    @classmethod
    def load_pedfile(cls, pedfile):
        df = pd.read_csv(
            pedfile, sep='\t',
            dtype={
                'familyId': object,
                'personId': object,
                'dadId': object,
                'momId': object,
                'gender': np.int32,
                'status': np.int32,
            }
        )
        assert set(cls.PED_COLUMNS) <= set(df.columns)
        return df

    def prepare(self, ped_df):
        assert set(self.PED_COLUMNS) <= set(ped_df.columns)
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

    def build(self, pedfile):
        ped_df = self.load_pedfile(pedfile)
        ped_df = self.prepare(ped_df)
        self.save(ped_df)
        return ped_df


class PrepareVariables(PrepareBase):

    def __init__(self, config, pedigree_df):
        super(PrepareVariables, self).__init__(config)
        self.pedigree_df = pedigree_df
        self.sample_ids = None

    def load_instrument(self, instrument_name, filenames):
        assert filenames
        assert all([os.path.exists(f) for f in filenames])

        instrument_names = [
            os.path.splitext(os.path.basename(f))[0]
            for f in filenames
        ]
        assert len(set(instrument_names)) == 1
        assert instrument_name == instrument_names[0]

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
            assert len(set([len(f.columns) for f in dataframes])) == 1
            df = pd.concat(dataframes, ignore_index=True)

        assert df is not None

        df = self._augment_person_ids(df)
        df = self._adjust_instrument_measure_names(instrument_name, df)
        return df

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
        with self.db.engine.begin() as connection:
            result = connection.execute(ins)
            measure_id = result.inserted_primary_key[0]
        if len(mdf) == 0:
            print('empty measure: {}'.format(measure.measure_id))
            return

        def convert(v): return v
        if measure.measure_type == MeasureType.categorical or \
                measure.measure_type == MeasureType.other:
            def convert(v):
                if type(v) in set([str, unicode]):
                    return unicode(remove_annoying_characters(v))
                else:
                    return unicode(v)

        values = OrderedDict()
        for _index, row in mdf.iterrows():
            pid = int(row[self.PID_COLUMN])
            k = (pid, measure_id)
            v = {
                self.PERSON_ID: pid,
                'measure_id': measure_id,
                'value': convert(row['value'])
            }
            if k in values:
                print("updating measure {} value {} with {}".format(
                    measure.measure_id,
                    values[k]['value'],
                    row['value'])
                )
            values[k] = v

        value_table = self.db.get_value_table(measure.measure_type)
        ins = value_table.insert()
        with self.db.engine.begin() as connection:
            connection.execute(ins, values.values())

    def _collect_instruments(self, dirname, instruments):
        for root, _dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                basename = os.path.basename(filename)
                name, ext = os.path.splitext(basename)
                if ext.lower() != '.csv':
                    continue
                print(root, filename)
                instruments[name].append(
                    os.path.abspath(os.path.join(root, filename))
                )

    def build(self, instruments_dirname):
        self.build_pheno_common()

        instruments = defaultdict(list)
        self._collect_instruments(instruments_dirname, instruments)
        for instrument_name, instrument_filenames in instruments.items():
            self.build_instrument(instrument_name, instrument_filenames)

    def _augment_person_ids(self, df):
        persons = self.get_persons()
        pid = pd.Series(df.index)
        for index, row in df.iterrows():
            p = persons.get(row[self.PERSON_ID])
            if p is None:
                pid[index] = np.nan
                print('measure for missing person: {}'.format(
                    row[self.PERSON_ID]))
            else:
                assert p is not None
                assert p.person_id == row[self.PERSON_ID]
                pid[index] = p.id

        df[self.PID_COLUMN] = pid
        df = df[np.logical_not(np.isnan(df[self.PID_COLUMN]))].copy()
        return df

    def build_pheno_common(self):
        pheno_common_measures = set(self.pedigree_df.columns) - \
            (set(self.PED_COLUMNS) | set(['sampleId', 'role']))

        df = self.pedigree_df.copy(deep=True)

        df.rename(columns={'personId': self.PERSON_ID}, inplace=True)

        assert self.PERSON_ID in df.columns
        df = self._augment_person_ids(df)

        for measure_name in pheno_common_measures:
            self.build_measure('pheno_common', measure_name, df)

    def build_measure(self, instrument_name, measure_name, df):
        if measure_name in self.config.skip.measures or \
                measure_name == self.PID_COLUMN:
            return
        mdf = df[[self.PERSON_ID, self.PID_COLUMN, measure_name]].dropna()
        mdf.rename(columns={measure_name: 'value'}, inplace=True)

        measure = self._build_measure(
            instrument_name, measure_name, mdf)
        print(instrument_name, measure_name, measure)
        self._save_measure(measure, mdf)

    def build_instrument(self, instrument_name, filenames):
        assert instrument_name is not None
        df = self.load_instrument(instrument_name, filenames)

        assert df is not None
        assert self.PERSON_ID in df.columns

        for measure_name in df.columns[1:]:
            self.build_measure(instrument_name, measure_name, df)
        return df

    @classmethod
    def check_values_type(cls, values):
        boolean = all([isinstance(v, bool) for v in values])
        if boolean:
            return bool

        try:
            vals = [v.strip() for v in values
                    if not (isinstance(v, float) or isinstance(v, int))]
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

    @staticmethod
    def _value_domain_list(unique_values):
        DOMAIN_MAX_DISPLAY = 5
        unique_values = sorted(unique_values)
        unique_values = [str(v) for v in unique_values]
        if len(unique_values) >= DOMAIN_MAX_DISPLAY:
            unique_values = unique_values[:DOMAIN_MAX_DISPLAY + 1]
            unique_values[DOMAIN_MAX_DISPLAY] = '...'
        return "{}".format(','.join([v for v in unique_values]))

    @staticmethod
    def _value_domain_range(unique_values):
        min_value = min(unique_values)
        max_value = max(unique_values)
        return "[{},{}]".format(min_value, max_value)

    def _default_measure(self, instrument_name, measure_name):
        measure = {
            'measure_type': MeasureType.other,
            'measure_name': measure_name,
            'instrument_name': instrument_name,
            'measure_id': '{}.{}'.format(instrument_name, measure_name),
            'individuals': None,
            'default_filter': None
        }
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
            print("checking values type ({}) for {}:{}".format(
                values.dtype, instrument_name, measure_name))
            values_type = self.check_values_type(unique_values)

        if values_type in set([str, bool, np.bool, np.dtype('bool')]):
            if self.check_categorical_rank(rank, individuals):
                measure.measure_type = MeasureType.categorical
                return measure
        elif values_type in set([int, float, np.float, np.int,
                                 np.dtype('int64'), np.dtype('float64')]):
            if self.check_continuous_rank(rank, individuals):
                measure.measure_type = MeasureType.continuous
                return measure
            if self.check_ordinal_rank(rank, individuals):
                measure.measure_type = MeasureType.continuous
                return measure
            if self.check_categorical_rank(rank, individuals):
                measure.measure_type = MeasureType.categorical
                return measure

        measure.measure_type = MeasureType.other
        return measure


class PrepareMetaMeasures(PrepareBase):

    def __init__(self, config):
        super(PrepareMetaMeasures, self).__init__(config)
        self.pheno = PhenoDB(dbfile=self.db.dbfile)
        self.pheno.load(meta=False)

    def build(self):
        measures = self.db.get_measures()
        for m in measures.values():
            self.build_meta_measure(m)

    def build_meta_measure(self, measure):
        print("processing meta measures for {}".format(measure.measure_id))
        df = self.pheno.get_measure_values_df(measure.measure_id)
        measure_type = measure.measure_type
        values = df[measure.measure_id]
        if measure_type in \
                set([MeasureType.continuous, MeasureType.ordinal]):
            min_value = values.values.min()
            max_value = values.values.max()
        else:
            min_value = None
            max_value = None
        if measure_type == MeasureType.continuous:
            values_domain = "[{}, {}]".format(min_value, max_value)
        else:
            values_domain = ",".join(sorted(values.unique()))

        meta = {
            'measure_id': measure.id,
            'min_value': min_value,
            'max_value': max_value,
            'values_domain': values_domain,
        }
        try:
            insert = self.db.meta_measure.insert().values(**meta)
            with self.db.engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            del meta['measure_id']
            update = self.db.meta_measure.update().values(**meta).where(
                self.db.meta_measure.c.measure_id == measure.id
            )
            with self.db.engine.begin() as connection:
                connection.execute(update)
