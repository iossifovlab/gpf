'''
Created on Jul 24, 2017

@author: lubo
'''
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Boolean, Float


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
            Column('variable_id', String(128),
                   primary_key=True, nullable=False),
            Column('table_name', String(64), nullable=False),
            Column('variable_name', String(64), nullable=False),
            Column('domain', String(64), ),
            Column('domain_choice_label', String(255)),
            Column('measurement_scale', String(16), ),
            Column('description', String(255)),
            Column('source', String(64)),
            Column('domain_rank', Integer()),
            Column('individuals', Integer()),
            Column('stats', String(16)),
            Column('min_value', Float()),
            Column('max_value', Float()),
            Column('value_domain', String(255))
        )
        self.meta_variable = Table(
            'meta_variable', self.metadata,
            Column('variable_id', String(128),
                   primary_key=True, nullable=False),
            Column('min_value', Float()),
            Column('max_value', Float(), ),
            Column('has_probands', Boolean(), ),
            Column('has_siblings', Boolean(),),
            Column('has_parents', Boolean(), ),
            Column('default_filter', String(128))
        )

    def _build_value_tables(self):
        self.value_continuous = Table(
            'value_continuous', self.metadata,
            Column('person_id', String(16),
                   primary_key=True, nullable=False),
            Column('variable_id', String(128),
                   primary_key=True, nullable=False),
            Column('family_id', String(32),  nullable=False),
            Column('person_role', String(8),  nullable=False),
            Column('value', Float(),  nullable=False)
        )
        self.value_ordinal = Table(
            'value_ordinal', self.metadata,
            Column('person_id', String(16),
                   primary_key=True, nullable=False),
            Column('variable_id', String(128),
                   primary_key=True, nullable=False),
            Column('family_id', String(32), nullable=False),
            Column('person_role', String(8), nullable=False),
            Column('value', Float(), nullable=False)
        )
        self.value_categorical = Table(
            'value_categorical', self.metadata,
            Column('person_id', String(16),
                   primary_key=True, nullable=False),
            Column('variable_id', String(128),
                   primary_key=True, nullable=False),
            Column('family_id', String(32),  nullable=False),
            Column('person_role', String(8), nullable=False),
            Column('value', String(127), nullable=False)
        )
        self.value_other = Table(
            'value_other', self.metadata,
            Column('person_id', String(16),
                   primary_key=True, nullable=False),
            Column('variable_id', String(128),
                   primary_key=True, nullable=False),
            Column('family_id', String(32), nullable=False),
            Column('person_role', String(8),  nullable=False),
            Column('value', String(127), nullable=False)
        )
