'''
Created on Aug 25, 2016

@author: lubo
'''
import os
import sqlite3

import pandas as pd
from pheno.utils.configuration import PhenoConfig


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

    def __init__(self, test=False):
        super(ManagerBase, self).__init__()
        if test:
            self.pheno_db = os.path.join(self.cache_dir, 'pheno_db_test.sql')
        else:
            self.pheno_db = os.path.join(self.cache_dir, 'pheno_db.sql')
        self.db = None

    def connect(self):
        self.db = sqlite3.connect(self.pheno_db)
        return self.db

    def is_connected(self):
        return self.db is not None

    def delete(self):
        assert self.db is None
        if os.path.exists(self.pheno_db):
            os.remove(self.pheno_db)

    def close(self):
        self.db.commit()
        self.db.close()
        self.db = None

    def create_db(self):
        if os.path.exists(self.pheno_db):
            raise ValueError("pheno db {} already exists".format(
                self.pheno_db))
        assert not self.is_connected()
        self.connect()
        self.db.executescript(_SCHEMA_)
        self.db.commit()
        self.close()


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

    def create_tables(self):
        self.connect()
        self.db.executescript(self.SCHEMA_CREATE)
        self.close()

    def __init__(self, test=False):
        super(PersonManager, self).__init__(test)

    def save(self, p):
        query = "INSERT OR REPLACE INTO pheno_db_person " \
            "(person_id, family_id, role, role_id, " \
            " gender, race, " \
            " collection, ssc_present) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        t = (p.person_id, p.family_id, p.role, p.role_id,
             p.gender, p.race,
             p.collection, p.ssc_present)
        self.db.execute(query, t)

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
