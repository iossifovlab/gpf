'''
Created on Aug 25, 2016

@author: lubo
'''
import os
import sqlite3

import pandas as pd
import numpy as np

import traceback


class ManagerBase(object):

    def __init__(self, dbfile, *args, **kwargs):
        super(ManagerBase, self).__init__(*args, **kwargs)
        self.db = None
        self.dbfile = dbfile

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
        # print("connecting to {}".format(filename))
        # traceback.print_stack()

        self.db = sqlite3.connect(self.dbfile, isolation_level="DEFERRED")
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

    def load(self, where=None):
        df = self.load_df(where)

        res = []
        for _index, row in df.iterrows():
            r = self.MODEL.create_from_df(row)
            res.append(r)
        return res

    def get(self, where):
        res = self.load(where)
        assert len(res) <= 1
        if res:
            return res[0]
        else:
            return None

    def _execute(self, query):
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
        return recs


class PersonModel(object):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS person (
        person_id varchar(16) NOT NULL PRIMARY KEY,
        family_id varchar(32) NOT NULL,
        role varchar(16) NOT NULL,
        role_id varchar(8) NOT NULL,
        role_order int NOT NULL,
        gender varchar(1) NULL,
        collection varchar(32) NULL,
        ssc_present bool NULL
    );
    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;
    DROP TABLE IF EXISTS person;
    COMMIT;
    """

    COLUMNS = [
        'person_id',
        'family_id',
        'role',
        'role_id',
        'role_order',
        'gender',
        'collection',
        'ssc_present',
        # 'sample_id',
    ]

    TABLE = 'person'

    def __init__(self):
        self.person_id = None
        self.family_id = None
        self.role = None
        self.role_id = None
        self.role_order = None
        self.gender = None
        self.collection = None
        self.ssc_present = None
        # self.sample_id = None

    @staticmethod
    def create_from_df(row):
        p = PersonModel()
        p.person_id = row['person_id']
        p.family_id = row['family_id']
        p.role = row['role']
        p.role_id = row['role_id']
        p.role_order = row['role_order']
        p.gender = row['gender']
        # p.sample_id = row['sample_id']
        # p.collection = row['collection']
        # p.ssc_present = row['ssc_present']

        return p

    @staticmethod
    def to_tuple(p):
        return (
            p.person_id,
            p.family_id,
            p.role,
            p.role_id,
            p.role_order,
            p.gender,
            p.collection,
            p.ssc_present,
            # p.sample_id,
        )


class PersonManager(ManagerBase):

    MODEL = PersonModel

    def __init__(self, *args, **kwargs):
        super(PersonManager, self).__init__(*args, **kwargs)


class VariableModel(object):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS variable (
        variable_id varchar(128) NOT NULL PRIMARY KEY,
        table_name varchar(64) NOT NULL,
        variable_name varchar(64) NOT NULL,
        domain varchar(64) NULL,
        domain_choice_label text NULL,
        measurement_scale varchar(16) NULL,
        description text NULL,
        source varchar(64) NULL,
        domain_rank integer NULL,
        individuals integer NULL,
        stats varchar(16) NULL,
        min_value real NULL,
        max_value real NULL,
        value_domain text NULL
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
        'min_value',
        'max_value',
        'value_domain',
    ]

    def __repr__(self):
        return "Variable({}, {}, {}, {})".format(
            self.variable_id,
            self.individuals,
            self.stats,
            self.value_domain)

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
        self.min_value = None
        self.max_value = None
        self.value_domain = None

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
            v.stats,
            v.min_value,
            v.max_value,
            v.value_domain,
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
        v.min_value = row['min_value']
        v.max_value = row['max_value']
        v.value_domain = row['value_domain']
        return v


class VariableManager(ManagerBase):

    MODEL = VariableModel

    def __init__(self, *args, **kwargs):
        super(VariableManager, self).__init__(*args, **kwargs)


class MetaVariableCorrelationModel(object):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS {table} (
        variable_id varchar(128) NOT NULL,
        correlation_with varchar(128) NOT NULL,
        role varchar(16) NOT NULL,
        gender varchar(1) NOT NULL,
        coeff real NULL,
        pvalue real NULL,
        PRIMARY KEY (variable_id, correlation_with, role, gender)
    );
    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP TABLE IF EXISTS {table};

    COMMIT;
    """

    TABLE = 'meta_variable_correlation'

    COLUMNS = [
        'variable_id',
        'correlation_with',
        'role',
        'gender',
        'coeff',
        'pvalue',
    ]

    def __init__(self):
        self.variable_id = None
        self.correlation_with = None
        self.role = None
        self.gender = None
        self.coeff = None
        self.pvalue = None

    @staticmethod
    def to_tuple(v):
        return (
            v.variable_id,
            v.correlation_with,
            v.role,
            v.gender,
            v.coeff,
            v.pvalue,
        )

    @staticmethod
    def create_from_df(row):
        v = MetaVariableModel()

        v.variable_id = row['variable_id']
        v.correlation_with = row['correlation_with']
        v.role = row['role']
        v.gender = row['gender']
        v.coeff = row['coeff']
        v.pvalue = row['pvalue']
        return v


class MetaVariableCorrelationManager(ManagerBase):

    MODEL = MetaVariableCorrelationModel

    def __init__(self, *args, **kwargs):
        super(MetaVariableCorrelationManager, self).__init__(*args, **kwargs)


class MetaVariableModel(object):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS {table} (
        variable_id varchar(128) NOT NULL PRIMARY KEY,
        min_value real NULL,
        max_value real NULL,
        has_probands bool NULL,
        has_siblings bool NULL,
        has_parents bool NULL,
        default_filter varchar(128) NULL
    );
    COMMIT;
    """

    SCHEMA_DROP = """
    BEGIN;

    DROP TABLE IF EXISTS {table};

    COMMIT;
    """

    TABLE = 'meta_variable'

    COLUMNS = [
        'variable_id',
        'min_value',
        'max_value',
        'has_probands',
        'has_siblings',
        'has_parents',
        'default_filter',
    ]

    def __init__(self):
        self.variable_id = None
        self.min_value = None
        self.max_value = None
        self.has_probands = None
        self.has_siblings = None
        self.has_parents = None
        self.default_filter = None

    def __repr__(self):
        return "MetaVariable({}, {}, {}, {}, {}, {})".format(
            self.variable_id,
            self.min_value,
            self.max_value,
            self.has_probands,
            self.has_siblings,
            self.has_parents)

    @staticmethod
    def to_tuple(v):
        return (
            v.variable_id,
            v.min_value,
            v.max_value,
            v.has_probands,
            v.has_siblings,
            v.has_parents,
            v.default_filter
        )

    @staticmethod
    def create_from_df(row):
        v = MetaVariableModel()

        v.variable_id = row['variable_id']
        v.min_value = row['min_value']
        v.max_value = row['max_value']
        v.has_probands = row['has_probands']
        v.has_siblings = row['has_siblings']
        v.has_parents = row['has_parents']
        v.default_filter = row['default_filter']
        # print("CREATE_FROM_DF:", v.default_filter, type(v.default_filter))
        return v


class MetaVariableManager(ManagerBase):

    MODEL = MetaVariableModel

    def __init__(self, *args, **kwargs):
        super(MetaVariableManager, self).__init__(*args, **kwargs)


class ValueModel(object):
    SCHEMA_CREATE = """
    BEGIN;

    CREATE TABLE IF NOT EXISTS {table} (
        person_id varchar(16) NOT NULL,
        variable_id varchar(128) NOT NULL,
        family_id varchar(32) NOT NULL,
        person_role varchar(8) NOT NULL,
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
            cls.value_encode(v.value)
        )

    @classmethod
    def create_from_df(cls, row):
        v = cls()

        v.family_id = row['family_id']
        v.person_id = row['person_id']
        v.person_role = row['person_role']
        v.variable_id = row['variable_id']
        v.value = cls.value_decode(row['value'])

        return v

    @classmethod
    def isnull(cls, value):
        if value is None:
            return True
        if isinstance(value, float) and np.isnan(value):
            return True
        if isinstance(value, str) and (value is None or value == 'nan'):
            return True
        if isinstance(value, unicode) and (value is None or value == 'nan'):
            return True

        return False

    @classmethod
    def value_encode(cls, val):
        if val is None:
            return None
        elif isinstance(val, unicode):
            return val
        elif isinstance(val, str):
            try:
                return str(val).encode('utf-8')
            except Exception as ex:
                print("cant encode value: |{}|".format(val))
                raise ex
        else:
            return str(val)

    @classmethod
    def value_decode(cls, val):
        if val is None:
            return None
        elif isinstance(val, unicode):
            return val
        elif isinstance(val, str):
            return str(val).decode('utf-8')
        else:
            return str(val)

    def __repr__(self):
        return "Value({},{},{})".format(
            self.variable_id, self.person_id, self.value)


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
    def value_encode(cls, val):
        return float(val)

    @classmethod
    def value_decode(cls, val):
        return float(val)


class FloatValueManager(ValueManager):

    MODEL = FloatValueModel

    def __init__(self, *args, **kwargs):
        super(FloatValueManager, self).__init__(*args, **kwargs)


class TextValueModel(ValueModel):
    TABLE = 'value_text'
    TYPE = str
    TYPE_NAME = 'text'
    TYPE_SQL = 'varchar(127)'


class TextValueManager(ValueManager):
    MODEL = TextValueModel

    def __init__(self, *args, **kwargs):
        super(TextValueManager, self).__init__(*args, **kwargs)


class RawValueModel(ValueModel):
    TABLE = 'value_raw'
    TYPE = str
    TYPE_NAME = 'text'
    TYPE_SQL = 'varchar(127)'


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

    @classmethod
    def value_encode(cls, val):
        return float(val)

    @classmethod
    def value_decode(cls, val):
        return float(val)


class ContinuousValueManager(ValueManager):
    MODEL = ContinuousValueModel

    def __init__(self, *args, **kwargs):
        super(ContinuousValueManager, self).__init__(*args, **kwargs)


class CategoricalValueModel(ValueModel):
    TABLE = 'value_categorical'
    TYPE = str
    TYPE_NAME = 'text'
    TYPE_SQL = 'varchar(127)'


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
    def value_encode(cls, val):
        return int(float(val))

    @classmethod
    def value_decode(cls, val):
        return int(float(val))


class OrdinalValueManager(ValueManager):
    MODEL = OrdinalValueModel

    def __init__(self, *args, **kwargs):
        super(OrdinalValueManager, self).__init__(*args, **kwargs)
