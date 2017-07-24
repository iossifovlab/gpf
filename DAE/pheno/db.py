'''
Created on Jul 24, 2017

@author: lubo
'''
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, Numeric, String, Boolean
from sqlalchemy.sql.sqltypes import VARCHAR, REAL, BOOLEAN, INTEGER, TEXT

TABLES = {
}


class DbManager(object):

    def __init__(self, dbfile):
        self.metadata = MetaData()
        self.engine = create_engine("sqlite:///{}".format(dbfile))

    def build(self):
        self._build_person_tables()
        self._build_variable_tables()
        self._build_value_tables()

        self.metadata.create_all(self.engine)

    def _build_person_tables(self):
        self.person = Table(
            'person', self.metadata,
            Column('person_id', String(16),
                   primary_key=True, nullable=False),
            Column('family_id', String(32), nullable=False),
            Column('role', String(16), nullable=False),
            Column('role_id', String(8),  nullable=False),
            Column('role_order', Integer(), nullable=False),
            Column('gender', String(1), ),
            Column('collection', String(32)),
            Column('ssc_present', Boolean())
        )

    def _build_variable_tables(self):
        self.variable = Table(
            'variable', self.metadata,
            Column('variable_id', VARCHAR(length=128),
                   primary_key=True, nullable=False),
            Column('table_name', VARCHAR(length=64), nullable=False),
            Column('variable_name', VARCHAR(length=64), nullable=False),
            Column('domain', VARCHAR(length=64), ),
            Column('domain_choice_label', TEXT()),
            Column('measurement_scale', VARCHAR(length=16), ),
            Column('description', TEXT()),
            Column('source', VARCHAR(length=64)),
            Column('domain_rank', INTEGER()),
            Column('individuals', INTEGER()),
            Column('stats', VARCHAR(length=16)),
            Column('min_value', REAL()),
            Column('max_value', REAL()),
            Column('value_domain', TEXT())
        )
        self.meta_variable = Table(
            'meta_variable', self.metadata,
            Column('variable_id', VARCHAR(length=128),
                   primary_key=True, nullable=False),
            Column('min_value', REAL()),
            Column('max_value', REAL(), ),
            Column('has_probands', BOOLEAN(), ),
            Column('has_siblings', BOOLEAN(),),
            Column('has_parents', BOOLEAN(), ),
            Column('default_filter', VARCHAR(length=128))
        )

    def _build_value_tables(self):
        self.value_continuous = Table(
            'value_continuous', self.metadata,
            Column('person_id', VARCHAR(length=16),
                   primary_key=True, nullable=False),
            Column('variable_id', VARCHAR(length=128),
                   primary_key=True, nullable=False),
            Column('family_id', VARCHAR(length=32),  nullable=False),
            Column('person_role', VARCHAR(length=8),  nullable=False),
            Column('value', REAL(),  nullable=False)
        )
        self.value_ordinal = Table(
            'value_ordinal', self.metadata,
            Column('person_id', VARCHAR(length=16),
                   primary_key=True, nullable=False),
            Column('variable_id', VARCHAR(length=128),
                   primary_key=True, nullable=False),
            Column('family_id', VARCHAR(length=32), nullable=False),
            Column('person_role', VARCHAR(length=8), nullable=False),
            Column('value', REAL(), nullable=False)
        )
        self.value_categorical = Table(
            'value_categorical', self.metadata,
            Column('person_id', VARCHAR(length=16),
                   primary_key=True, nullable=False),
            Column('variable_id', VARCHAR(length=128),
                   primary_key=True, nullable=False),
            Column('family_id', VARCHAR(length=32),  nullable=False),
            Column('person_role', VARCHAR(length=8), nullable=False),
            Column('value', VARCHAR(length=127), nullable=False)
        )
        self.value_other = Table(
            'value_other', self.metadata,
            Column('person_id', VARCHAR(length=16),
                   primary_key=True, nullable=False),
            Column('variable_id', VARCHAR(length=128),
                   primary_key=True, nullable=False),
            Column('family_id', VARCHAR(length=32), nullable=False),
            Column('person_role', VARCHAR(length=8),  nullable=False),
            Column('value', VARCHAR(length=127), nullable=False)
        )
