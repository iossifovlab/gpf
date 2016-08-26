'''
Created on Aug 25, 2016

@author: lubo
'''
import os
import sqlite3

import pandas as pd
from pheno.utils.configuration import PhenoConfig
import sys


_SCHEMA_ = """
BEGIN;
CREATE TABLE "pheno_db_person" (
    "person_id" varchar(32) NOT NULL,
    "role" varchar(16) NOT NULL,
    "role_id" varchar(8) NOT NULL,
    "gender" varchar(1) NOT NULL,
    "race" varchar(32) NOT NULL,
    "family_id" varchar(16) NOT NULL,
    "collection" varchar(64) NULL,
    "ssc_present" bool NULL
);

CREATE TABLE "pheno_db_valuefloat" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "family_id" varchar(64) NOT NULL,
    "person_id" varchar(64) NOT NULL,
    "person_role" varchar(16) NOT NULL,
    "variable_id" varchar(255) NOT NULL,
    "value" real NOT NULL
);

CREATE TABLE "pheno_db_variabledescriptor" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "source" varchar(32) NOT NULL,
    "table_name" varchar(64) NOT NULL,
    "variable_name" varchar(127) NOT NULL,
    "variable_category" varchar(127) NULL,
    "variable_id" varchar(255) NOT NULL UNIQUE,
    "domain" varchar(127) NOT NULL,
    "domain_choice_label" varchar(255) NULL,
    "measurement_scale" varchar(32) NOT NULL,
    "regards_mother" bool NULL,
    "regards_father" bool NULL,
    "regards_proband" bool NULL,
    "regards_sibling" bool NULL,
    "regards_family" bool NULL,
    "regards_other" bool NULL,
    "variable_notes" text NULL,
    "is_calculated" bool NOT NULL,
    "calculation_documentation" text NULL,
    "has_values" bool NULL,
    "domain_rank" integer NULL,
    "individuals" integer NULL
);

CREATE INDEX "pheno_db_person_a8452ca7" ON "pheno_db_person" ("person_id");
CREATE INDEX "pheno_db_person_29a7e964" ON "pheno_db_person" ("role");
CREATE INDEX "pheno_db_person_84566833" ON "pheno_db_person" ("role_id");
CREATE INDEX "pheno_db_person_cc90f191" ON "pheno_db_person" ("gender");
CREATE INDEX "pheno_db_person_2e2a7a2e" ON "pheno_db_person" ("race");
CREATE INDEX "pheno_db_person_0caa70f7" ON "pheno_db_person" ("family_id");

CREATE INDEX "pheno_db_variabledescriptor_ad5f82e8" ON "pheno_db_variabledescriptor" ("domain");
CREATE INDEX "pheno_db_valuefloat_0caa70f7" ON "pheno_db_valuefloat" ("family_id");
CREATE INDEX "pheno_db_valuefloat_a8452ca7" ON "pheno_db_valuefloat" ("person_id");
CREATE INDEX "pheno_db_valuefloat_45b4d26c" ON "pheno_db_valuefloat" ("person_role");
CREATE INDEX "pheno_db_valuefloat_59bc5ce5" ON "pheno_db_valuefloat" ("variable_id");
CREATE INDEX "pheno_db_valuefloat_161c9927" ON "pheno_db_valuefloat" ("descriptor_id");

COMMIT;
"""


class ManagerBase(PhenoConfig):

    def __init__(self, config=None, *args, **kwargs):
        super(ManagerBase, self).__init__(*args, **kwargs)
        if config is not None:
            self.config = config

        self.pheno_db = os.path.join(
            self['cache', 'dir'], 'pheno_db.sql')
        self.db = None

    def connect(self):
        if self.db is not None:
            return self.db
        self.db = sqlite3.connect(self.pheno_db)
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

    def __enter__(self):
        print("ManagerBase enter called...")
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("ManagerBase exit called...")
        if exc_type is not None:
            print("Exception in ManagerBase: {}: {}\n{}".format(
                exc_type, exc_value, traceback))
        self.close()
        return True


class PersonModel(object):

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


class PersonManager(ManagerBase):
    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS "pheno_db_person" (
        "person_id" varchar(32) NOT NULL PRIMARY KEY,
        "family_id" varchar(16) NOT NULL,
        "role" varchar(16) NOT NULL,
        "role_id" varchar(8) NOT NULL,
        "gender" varchar(1) NULL,
        "race" varchar(32) NULL,
        "collection" varchar(64) NULL,
        "ssc_present" bool NULL
    );
    COMMIT;
    """

    def __init__(self, *args, **kwargs):
        super(PersonManager, self).__init__(*args, **kwargs)

    def save(self, p):
        query = "INSERT OR REPLACE INTO pheno_db_person " \
            "(person_id, family_id, role, role_id, " \
            " gender, race, " \
            " collection, ssc_present) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        t = (p.person_id, p.family_id, p.role, p.role_id,
             p.gender, p.race,
             p.collection, p.ssc_present)
        self.db.execute(query, t)

    def save_df(self, df):
        for _index, row in df.iterrows():
            p = PersonModel.create_from_df(row)
            self.save(p)
        self.db.commit()

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

    def _build_select(self, where):
        query = "SELECT "\
            "person_id, family_id, role, role_id, "\
            "gender, race, "\
            "collection, ssc_present "\
            "FROM pheno_db_person "
        if where is None:
            query += ";"
        else:
            query += " WHERE {};".format(where)
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

        df = pd.DataFrame.from_records(recs, columns=self.COLUMNS)
        return df


class VariableModel(object):
    TABLE = 'pheno_db_variable'

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


class VariableManager(ManagerBase):

    SCHEMA_CREATE = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS "pheno_db_variable" (
        "variable_id" varchar(255) NOT NULL PRIMARY KEY,
        "table_name" varchar(64) NOT NULL,
        "variable_name" varchar(127) NOT NULL,
        "domain" varchar(127) NOT NULL,
        "domain_choice_label" varchar(255) NULL,
        "measurement_scale" varchar(32) NOT NULL,
        "description" text NULL,
        "has_values" bool NULL,
        "domain_rank" integer NULL,
        "individuals" integer NULL
    );
    COMMIT;
    """

    MODEL = VariableModel
    INSERT = "INSERT OR REPLACE INTO {} ({}) VALUES ({})".format(
        VariableModel.TABLE,
        ', '.join(VariableModel.COLUMNS),
        ', '.join(['?' for _i in VariableModel.COLUMNS])
    )

    def __init__(self, test=False):
        super(VariableManager, self).__init__(test)

    def save(self, obj):
        t = self.MODEL.to_tuple(obj)
        sys.stderr.write('.')
        self.db.execute(self.INSERT, t)
