'''
Created on Aug 31, 2017

@author: lubo
'''
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, String, Float


class DbManager(object):

    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.metadata = MetaData()
        self.engine = create_engine("sqlite:///{}".format(dbfile))

    def build(self):
        self._build_browser_tables()

    def _build_browser_tables(self):
        self.variable_browser = Table(
            'variable_browser', self.metadata,
            Column('measure_id', String(128),
                   nullable=False, index=True, unique=True, primary_key=True),
            Column('instrument_name', String(64), nullable=False, index=True),
            Column('measure_name', String(64), nullable=False, index=True),
            Column('figure_distribution_small', String(256)),
            Column('figure_distribution', String(256)),

            Column('values_domain', String(256)),

            Column('figure_correlation_nviq_small', String(256)),
            Column('figure_correlation_nviq', String(256)),
            Column('pvalue_correlation_nviq_male', Float()),
            Column('pvalue_correlation_nviq_female', Float()),

            Column('figure_correlation_age_small', String(256)),
            Column('figure_correlation_age', String(256)),
            Column('pvalue_correlation_age_male', Float()),
            Column('pvalue_correlation_age_female', Float()),

        )

    def save(self, variable_browser):
        try:
            insert = self.variable_browser. \
                insert().values(**variable_browser)
            with self.engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            measure_id = variable_browser['measure_id']
            del variable_browser['measure_id']
            update = self.variable_browser.\
                update().values(**variable_browser).where(
                    self.variable_browser.c.measure_id == measure_id
                )
            with self.engine.begin() as connection:
                connection.execute(update)
