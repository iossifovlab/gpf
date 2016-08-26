'''
Created on Aug 25, 2016

@author: lubo
'''
import os
import sqlite3

import pandas as pd
from pheno.utils.configuration import PhenoConfig
import traceback


class ManagerBase(PhenoConfig):

    def __init__(self, *args, **kwargs):
        super(ManagerBase, self).__init__(*args, **kwargs)
        self.db = None

    @classmethod
    def insert(cls):
        query = "INSERT OR REPLACE INTO {} ({}) VALUES ({})".format(
            cls.MODEL.TABLE,
            ', '.join(cls.MODEL.COLUMNS),
            ', '.join(['?' for _i in cls.MODEL.COLUMNS])
        )
        return query

    @classmethod
    def select(cls):
        query = "SELECT {} FROM {} ".format(
            ', '.join(cls.MODEL.COLUMNS),
            cls.MODEL.TABLE
        )
        return query

    def connect(self):
        if self.db is not None:
            return self.db
        filename = os.path.join(
            self['cache', 'dir'], 'pheno_db.sql')

        self.db = sqlite3.connect(filename)
        return self.db

    def is_connected(self):
        return self.db is not None

    def delete(self):
        assert self.db is None
        if os.path.exists(self.pheno_db):
            os.remove(self.pheno_db)

    def close(self):
        if self.db is None:
            return
        self.db.commit()
        self.db.close()
        self.db = None

    def create_tables(self):
        self.db.executescript(self.SCHEMA_CREATE)
        self.db.commit()

    def drop_tables(self):
        self.db.executescript(self.SCHEMA_DROP)
        self.db.commit()

    def __enter__(self):
        print("ManagerBase enter called...")
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        print("ManagerBase exit called...")
        if exc_type is not None:
            print("Exception in ManagerBase: {}: {}\n{}".format(
                exc_type, exc_value, tb))
            traceback.print_tb(tb)
        self.db.commit()
        self.db.close()
        return True

    def save(self, obj):
        t = self.MODEL.to_tuple(obj)
        self.db.execute(self.insert(), t)

    def save_df(self, df):
        for _index, row in df.iterrows():
            v = self.MODEL.create_from_df(row)
            self.save(v)
        self.db.commit()

    def _build_select(self, where):
        if where is None:
            query = self.select() + ";"
        else:
            query = self.select() + " WHERE {};".format(where)
        return query

    def load_df(self, where=None):
        query = self._build_select(where)

        recs = []
        cursor = self.db.cursor()
        cursor.execute(query)
        rows = cursor.fetchmany(size=200)
        while rows:
            recs.extend(rows)
            rows = cursor.fetchmany(size=200)
        self.db.commit()

        df = pd.DataFrame.from_records(recs, columns=self.MODEL.COLUMNS)
        return df


class PersonModel(object):
    COLUMNS = [
        'person_id',
        'family_id',
        'role',
        'role_id',
        'gender',
        'race',
        'collection',
        'ssc_present',
    ]

    TABLE = 'person'

    def __init__(self):
        self.person_id = None
        self.family_id = None
        self.role = None
        self.role_id = None
        self.gender = None
        self.race = None
        self.collection = None
        self.ssc_present = None

    @staticmethod
    def create_from_df(row):
        p = PersonModel()
        p.person_id = row['person_id']
        p.family_id = row['family_id']
        p.role = row['role']
        p.role_id = row['role_id']
        p.gender = row['gender']
        p.race = row['race']
        p.collection = row['collection']
        p.ssc_present = row['ssc_present']

        return p

    @staticmethod
    def to_tuple(p):
        return (
            p.person_id,
            p.family_id,
            p.role,
            p.role_id,
            p.gender,
            p.race,
            p.collection,
            p.ssc_present
        )


class PersonManager(ManagerBase):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS person (
        person_id varchar(32) NOT NULL PRIMARY KEY,
        family_id varchar(16) NOT NULL,
        role varchar(16) NOT NULL,
        role_id varchar(8) NOT NULL,
        gender varchar(1) NULL,
        race varchar(32) NULL,
        collection varchar(64) NULL,
        ssc_present bool NULL
    );
    COMMIT;
    """

    MODEL = PersonModel

    def __init__(self, *args, **kwargs):
        super(PersonManager, self).__init__(*args, **kwargs)


class VariableModel(object):
    TABLE = 'variable'

    COLUMNS = [
        'variable_id',
        'table_name',
        'variable_name',
        'domain',
        'domain_choice_label',
        'measurement_scale',
        'description',
        'has_values',
        'domain_rank',
        'individuals',
    ]

    def __init__(self):
        self.variable_id = None
        self.table_name = None
        self.variable_name = None
        self.domain = None
        self.domain_choice_label = None
        self.measurement_scale = None
        self.description = None
        self.has_values = None
        self.domain_rank = None
        self.individuals = None

    @staticmethod
    def to_tuple(v):
        choice_label = None
        if isinstance(v.domain_choice_label, str):
            choice_label = v.domain_choice_label.decode('utf-8')
        return (
            v.variable_id, v.table_name, v.variable_name,
            v.domain,
            choice_label,
            v.measurement_scale,
            v.description,
            v.has_values, v.domain_rank, v.individuals,
        )

    @staticmethod
    def create_from_df(row):
        v = VariableModel()

        v.variable_id = row['variable_id']
        v.table_name = row['table_name']
        v.domain = row['domain']
        v.domain_choice_label = row['domain_choice_label']
        v.measurement_scale = row['measurement_scale']
        v.description = row['description']
        v.has_values = row['has_values']
        v.domain_rank = row['domain_rank']
        v.individuals = row['individuals']

        return v


class VariableManager(ManagerBase):

    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS variable (
        variable_id varchar(255) NOT NULL PRIMARY KEY,
        table_name varchar(64) NOT NULL,
        variable_name varchar(127) NOT NULL,
        domain varchar(127) NOT NULL,
        domain_choice_label varchar(255) NULL,
        measurement_scale varchar(32) NOT NULL,
        description text NULL,
        has_values bool NULL,
        domain_rank integer NULL,
        individuals integer NULL
    );
    COMMIT;
    """

    MODEL = VariableModel

    def __init__(self, *args, **kwargs):
        super(VariableManager, self).__init__(*args, **kwargs)


class FloatValueModel(object):
    TABLE = 'value_float'

    COLUMNS = [
        'family_id',
        'person_id',
        'person_role',
        'variable_id',
        'value',
    ]

    def __init__(self):
        self.family_id = None
        self.person_id = None
        self.person_role = None
        self.variable_id = None
        self.value = None

    @staticmethod
    def to_tuple(v):
        return (
            v.family_id,
            v.person_id,
            v.person_role,
            v.variable_id,
            v.value
        )

    @staticmethod
    def create_from_df(row):
        v = FloatValueModel()

        v.family_id = row['family_id']
        v.person_id = row['person_id']
        v.person_role = row['person_role']
        v.variable_id = row['variable_id']
        v.value = row['value']

        return v


class FloatValueManager(ManagerBase):
    SCHEMA_CREATE = """
    BEGIN;

    CREATE TABLE IF NOT EXISTS value_float (
        person_id varchar(64) NOT NULL,
        variable_id varchar(255) NOT NULL,
        family_id varchar(64) NOT NULL,
        person_role varchar(16) NOT NULL,
        value real NOT NULL,
        PRIMARY KEY (person_id, variable_id)
    );
    CREATE INDEX IF NOT EXISTS "value_float_person_id" 
        ON "value_float" ("person_id");
    CREATE INDEX IF NOT EXISTS "value_float_family_id" 
        ON "value_float" ("family_id");
    CREATE INDEX IF NOT EXISTS "value_float_person_role" 
        ON "value_float" ("person_role");
    CREATE INDEX IF NOT EXISTS "value_float_variable_id" 
        ON "value_float" ("variable_id");

    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP INDEX IF EXISTS "value_float_person_id";
    DROP INDEX IF EXISTS "value_float_family_id";
    DROP INDEX IF EXISTS "value_float_person_role";
    DROP INDEX IF EXISTS "value_float_variable_id";

    DROP TABLE IF EXISTS "value_float";

    COMMIT;
    """

    MODEL = FloatValueModel

    def __init__(self, *args, **kwargs):
        super(FloatValueManager, self).__init__(*args, **kwargs)
