'''
Created on Aug 25, 2016

@author: lubo
'''
import os
import sqlite3

import pandas as pd
import numpy as np

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

        self.db = sqlite3.connect(filename, isolation_level="DEFERRED")
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

    @classmethod
    def schema_create(cls):
        return cls.MODEL.SCHEMA_CREATE.format(table=cls.MODEL.TABLE)

    @classmethod
    def schema_drop(cls):
        return cls.MODEL.SCHEMA_DROP.format(table=cls.MODEL.TABLE)

    def create_tables(self):
        self.db.executescript(self.schema_create())
        self.db.commit()

    def drop_tables(self):
        self.db.executescript(self.schema_drop())
        self.db.commit()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        res = True
        if exc_type is not None:
            print("Exception in ManagerBase: {}: {}\n{}".format(
                exc_type, exc_value, tb))
            traceback.print_tb(tb)
            res = None

        self.db.commit()
        self.db.close()
        return res

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
        if cursor is None:
            raise ValueError("can't create cursor...")
        cursor.execute(query)
        rows = cursor.fetchmany(size=200)
        while rows:
            recs.extend(rows)
            rows = cursor.fetchmany(size=200)
        self.db.commit()

        df = pd.DataFrame.from_records(recs, columns=self.MODEL.COLUMNS)
        return df


class PersonModel(object):
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

    MODEL = PersonModel

    def __init__(self, *args, **kwargs):
        super(PersonManager, self).__init__(*args, **kwargs)


class VariableModel(object):
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
        source varchar(64) NULL,
        domain_rank integer NULL,
        individuals integer NULL,
        stats varchar(32) NULL
    );
    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP TABLE IF EXISTS variable;

    COMMIT;
    """

    TABLE = 'variable'

    COLUMNS = [
        'variable_id',
        'table_name',
        'variable_name',
        'domain',
        'domain_choice_label',
        'measurement_scale',
        'description',
        'source',
        'domain_rank',
        'individuals',
        'stats',
    ]

    def __repr__(self):
        return "Variable({}, {}, {}, {}, {})".format(
            self.variable_id,
            self.domain,
            self.domain_choice_label,
            self.measurement_scale,
            self.domain_rank)

    def __init__(self):
        self.variable_id = None
        self.table_name = None
        self.variable_name = None
        self.domain = None
        self.domain_choice_label = None
        self.measurement_scale = None
        self.description = None
        self.source = None
        self.domain_rank = None
        self.individuals = None
        self.stats = None

    @staticmethod
    def to_tuple(v):
        choice_label = None
        if isinstance(v.domain_choice_label, str):
            choice_label = v.domain_choice_label
        elif isinstance(v.domain_choice_label, unicode):
            choice_label = v.domain_choice_label
        return (
            v.variable_id, v.table_name, v.variable_name,
            v.domain,
            choice_label,
            v.measurement_scale,
            v.description,
            v.source,
            v.domain_rank,
            v.individuals,
            v.stats
        )

    @staticmethod
    def create_from_df(row):
        v = VariableModel()

        v.variable_id = row['variable_id']
        v.table_name = row['table_name']
        v.variable_name = row['variable_name']
        v.domain = row['domain']
        if isinstance(row['domain_choice_label'], str):
            v.domain_choice_label = (
                row['domain_choice_label']).encode('utf-8')
        elif isinstance(row['domain_choice_label'], unicode):
            v.domain_choice_label = (
                row['domain_choice_label']).encode('utf-8')

        v.measurement_scale = row['measurement_scale']
        v.description = (row['description']).encode('utf-8')
        v.source = row['source']
        v.domain_rank = row['domain_rank']
        v.individuals = row['individuals']
        v.stats = row['stats']

        return v


class VariableManager(ManagerBase):

    MODEL = VariableModel

    def __init__(self, *args, **kwargs):
        super(VariableManager, self).__init__(*args, **kwargs)


class ValueModel(object):
    SCHEMA_CREATE = """
    BEGIN;

    CREATE TABLE IF NOT EXISTS {table} (
        person_id varchar(64) NOT NULL,
        variable_id varchar(255) NOT NULL,
        family_id varchar(64) NOT NULL,
        person_role varchar(16) NOT NULL,
        value {sql_type} NOT NULL,
        PRIMARY KEY (person_id, variable_id)
    );
    CREATE INDEX IF NOT EXISTS {table}_person_id
        ON {table} (person_id);
    CREATE INDEX IF NOT EXISTS {table}_family_id
        ON {table} (family_id);
    CREATE INDEX IF NOT EXISTS {table}_person_role
        ON {table} (person_role);
    CREATE INDEX IF NOT EXISTS {table}_variable_id
        ON {table} (variable_id);

    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP INDEX IF EXISTS {table}_person_id;
    DROP INDEX IF EXISTS {table}_family_id;
    DROP INDEX IF EXISTS {table}_person_role;
    DROP INDEX IF EXISTS {table}_variable_id;

    DROP TABLE IF EXISTS {table};

    COMMIT;
    """

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

    @classmethod
    def to_tuple(cls, v):
        return (
            v.family_id,
            v.person_id,
            v.person_role,
            v.variable_id,
            cls.value_convert(v.value)
        )

    @classmethod
    def create_from_df(cls, row):
        v = cls()

        v.family_id = row['family_id']
        v.person_id = row['person_id']
        v.person_role = row['person_role']
        v.variable_id = row['variable_id']
        v.value = row['value']

        return v

    @classmethod
    def isnull(cls, value):
        if isinstance(value, float) and np.isnan(value):
            return True
        if isinstance(value, str) and value is None:
            return True

        return False


class ValueManager(ManagerBase):

    def __init__(self, *args, **kwargs):
        super(ValueManager, self).__init__(*args, **kwargs)

    @classmethod
    def schema_create(cls):
        return cls.MODEL.SCHEMA_CREATE.format(
            table=cls.MODEL.TABLE,
            sql_type=cls.MODEL.TYPE_SQL)

    def load_values(self, variable, where=None):
        query = "variable_id = '{}'".format(variable.variable_id)
        if where is not None:
            query = "({}) and ({})".format(query, where)
        df = self.load_df(query)
        return df


class FloatValueModel(ValueModel):
    TABLE = 'value_float'
    TYPE = float
    TYPE_NAME = 'float'
    TYPE_SQL = 'real'

    @classmethod
    def value_convert(cls, val):
        return float(val)


class FloatValueManager(ValueManager):

    MODEL = FloatValueModel

    def __init__(self, *args, **kwargs):
        super(FloatValueManager, self).__init__(*args, **kwargs)


class TextValueModel(ValueModel):
    TABLE = 'value_text'
    TYPE = str
    TYPE_NAME = 'text'
    TYPE_SQL = 'varchar(255)'

    @classmethod
    def value_convert(cls, val):
        return str(val).decode('utf-8')


class TextValueManager(ValueManager):
    MODEL = TextValueModel

    def __init__(self, *args, **kwargs):
        super(TextValueManager, self).__init__(*args, **kwargs)


class RawValueModel(ValueModel):
    TABLE = 'value_raw'
    TYPE = str
    TYPE_NAME = 'text'
    TYPE_SQL = 'varchar(255)'

    @classmethod
    def value_convert(cls, val):
        return str(val).decode('utf-8')


class RawValueManager(ValueManager):
    MODEL = RawValueModel

    def __init__(self, *args, **kwargs):
        super(RawValueManager, self).__init__(*args, **kwargs)


class ContinuousValueModel(ValueModel):
    TABLE = 'value_continuous'
    TYPE = float
    TYPE_NAME = 'float'
    TYPE_SQL = 'real'

    @classmethod
    def value_convert(cls, val):
        return float(val)


class ContinuousValueManager(ValueManager):
    MODEL = ContinuousValueModel

    def __init__(self, *args, **kwargs):
        super(ContinuousValueManager, self).__init__(*args, **kwargs)


class CategoricalValueModel(ValueModel):
    TABLE = 'value_categorical'
    TYPE = str
    TYPE_NAME = 'text'
    TYPE_SQL = 'varchar(255)'

    @classmethod
    def value_convert(cls, val):
        return str(val).decode('utf-8')


class CategoricalValueManager(ValueManager):
    MODEL = CategoricalValueModel

    def __init__(self, *args, **kwargs):
        super(CategoricalValueManager, self).__init__(*args, **kwargs)


class OrdinalValueModel(ValueModel):
    TABLE = 'value_ordinal'
    TYPE = int
    TYPE_NAME = 'int'
    TYPE_SQL = 'integer'

    @classmethod
    def value_convert(cls, val):
        return int(float(val))


class OrdinalValueManager(ValueManager):
    MODEL = OrdinalValueModel

    def __init__(self, *args, **kwargs):
        super(OrdinalValueManager, self).__init__(*args, **kwargs)
