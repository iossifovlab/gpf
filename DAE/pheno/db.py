'''
Created on Jul 24, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Float, Enum, \
    ForeignKey
from sqlalchemy.sql import select

from variants.attributes import Sex, Status, Role
from pheno.common import MeasureType
from sqlalchemy.sql.schema import UniqueConstraint, PrimaryKeyConstraint


class DbManager(object):

    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.metadata = MetaData()
        if self.dbfile == 'memory':
            self.engine = create_engine("sqlite://")
        else:
            self.engine = create_engine("sqlite:///{}".format(dbfile))

    def build(self):
        self._build_person_tables()
        self._build_measure_tables()
        self._build_value_tables()

        self.metadata.create_all(self.engine)

    def _build_person_tables(self):
        self.family = Table(
            'family', self.metadata,
            Column('id', Integer(), primary_key=True),
            Column('family_id', String(64), nullable=False,
                   unique=True, index=True),
        )
        self.person = Table(
            'person', self.metadata,
            Column('id', Integer(), primary_key=True),
            Column('family_id', ForeignKey('family.id')),
            Column('person_id', String(16), nullable=False, index=True),
            Column('role', Enum(Role), nullable=False),
            Column('status', Enum(Status),
                   nullable=False, default=Status.unaffected),
            Column('gender', Enum(Sex), nullable=False),
            Column('sample_id', String(16), nullable=True),
            UniqueConstraint('family_id', 'person_id', name='person_key'),
        )

    def _build_measure_tables(self):
        self.measure = Table(
            'measure', self.metadata,
            Column('id', Integer(), primary_key=True),
            Column('measure_id', String(128),
                   nullable=False, index=True, unique=True),
            Column('instrument_name', String(64), nullable=False, index=True),
            Column('measure_name', String(64), nullable=False, index=True),
            Column('description', String(255)),
            Column('measure_type', Enum(MeasureType), index=True),
            Column('individuals', Integer()),
            Column('default_filter', String(255)),
            Column('min_value', Float(), nullable=True),
            Column('max_value', Float(), nullable=True),
            Column('values_domain', String(255), nullable=True),
            Column('rank', Integer(), nullable=True),
            UniqueConstraint('instrument_name', 'measure_name',
                             name='measure_key'),
        )

    def _build_value_tables(self):
        self.value_continuous = Table(
            'value_continuous', self.metadata,
            Column('person_id', ForeignKey('person.id')),
            Column('measure_id', ForeignKey('measure.id')),
            Column('value', Float(),  nullable=False),
            PrimaryKeyConstraint('person_id', 'measure_id')
        )
        self.value_ordinal = Table(
            'value_ordinal', self.metadata,
            Column('person_id', ForeignKey('person.id')),
            Column('measure_id', ForeignKey('measure.id')),
            Column('value', Float(),  nullable=False),
            PrimaryKeyConstraint('person_id', 'measure_id')
        )
        self.value_categorical = Table(
            'value_categorical', self.metadata,
            Column('person_id', ForeignKey('person.id')),
            Column('measure_id', ForeignKey('measure.id')),
            Column('value', String(127),  nullable=False),
            PrimaryKeyConstraint('person_id', 'measure_id')
        )
        self.value_other = Table(
            'value_other', self.metadata,
            Column('person_id', ForeignKey('person.id')),
            Column('measure_id', ForeignKey('measure.id')),
            Column('value', String(127),  nullable=False),
            PrimaryKeyConstraint('person_id', 'measure_id')
        )

    def get_value_table(self, value_type):
        if isinstance(value_type, str) or isinstance(value_type, str):
            value_type = MeasureType.from_str(value_type)

        if value_type == MeasureType.continuous:
            return self.value_continuous
        elif value_type == MeasureType.ordinal:
            return self.value_ordinal
        elif value_type == MeasureType.categorical:
            return self.value_categorical
        elif value_type == MeasureType.raw or value_type == MeasureType.text:
            return self.value_other
        else:
            raise ValueError("unsupported value type: {}".format(value_type))

    def get_families(self):
        s = select([self.family])
        with self.engine.connect() as connection:
            families = connection.execute(s).fetchall()
        families = {f.family_id: f for f in families}
        return families

    def get_persons(self):
        s = select([
            self.person.c.id,
            self.person.c.person_id,
            self.family.c.family_id,
            self.person.c.role,
            self.person.c.status,
            self.person.c.gender,
        ])
        s = s.select_from(self.person.join(self.family))
        with self.engine.connect() as connection:
            persons = connection.execute(s).fetchall()
        persons = {p.person_id: p for p in persons}
        return persons

    def get_measures(self):
        s = select([
            self.measure.c.id,
            self.measure.c.measure_id,
            self.measure.c.instrument_name,
            self.measure.c.measure_name,
            self.measure.c.measure_type,
        ])
        s = s.select_from(self.measure)
        with self.engine.begin() as connection:
            measures = connection.execute(s).fetchall()
        measures = {
            m.measure_id: m for m in measures
        }
        return measures
