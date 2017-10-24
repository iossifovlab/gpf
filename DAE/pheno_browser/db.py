'''
Created on Aug 31, 2017

@author: lubo
'''
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, String, Float, Enum
from sqlalchemy.sql import select
from pheno.common import MeasureType
# import traceback


class DbManager(object):

    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.metadata = MetaData()
        self.engine = create_engine("sqlite:///{}".format(dbfile))

    def build(self):
        self._build_browser_tables()

        self.metadata.create_all(self.engine)

    def _build_browser_tables(self):
        self.variable_browser = Table(
            'variable_browser', self.metadata,
            Column('measure_id', String(128),
                   nullable=False, index=True, unique=True, primary_key=True),
            Column('instrument_name', String(64), nullable=False, index=True),
            Column('measure_name', String(64), nullable=False, index=True),
            Column('measure_type', Enum(MeasureType), nullable=False),
            Column('values_domain', String(256)),

            Column('figure_distribution_small', String(256)),
            Column('figure_distribution', String(256)),


            Column('figure_correlation_nviq_small', String(256)),
            Column('figure_correlation_nviq', String(256)),
            Column('pvalue_correlation_nviq_male', Float()),
            Column('pvalue_correlation_nviq_female', Float()),

            Column('figure_correlation_age_small', String(256)),
            Column('figure_correlation_age', String(256)),
            Column('pvalue_correlation_age_male', Float()),
            Column('pvalue_correlation_age_female', Float()),

        )

    def save(self, v):
        try:
            insert = self.variable_browser. \
                insert().values(**v)
            with self.engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            # traceback.print_exc()
            measure_id = v['measure_id']

            del v['measure_id']
            update = self.variable_browser.\
                update().values(**v).where(
                    self.variable_browser.c.measure_id == measure_id
                )
            with self.engine.begin() as connection:
                connection.execute(update)

    def get(self, measure_id):
        s = select([self.variable_browser])
        s = s.where(self.variable_browser.c.measure_id == measure_id)
        with self.engine.connect() as connection:
            vs = connection.execute(s).fetchall()
            if vs:
                return vs[0]
            else:
                return None
