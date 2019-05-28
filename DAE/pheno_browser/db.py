'''
Created on Aug 31, 2017

@author: lubo
'''
from __future__ import unicode_literals
from builtins import object

# import os

from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, String, Float, Enum, func, or_
from sqlalchemy.sql import select
from pheno.common import MeasureType
# import traceback
import pandas as pd


class DbManager(object):

    def __init__(self, dbfile):
        # assert os.path.exists(dbfile), dbfile
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
            Column('description', String(256)),
            Column('values_domain', String(256)),

            Column('figure_distribution_small', String(256)),
            Column('figure_distribution', String(256)),
        )

        self.regressions = Table(
            'regressions', self.metadata,
            Column('regression_name', String(128),
                   nullable=False, index=True),
            Column('measure_id', String(128), nullable=False, index=True),
            Column('regression_measure_id', String(128),
                   nullable=False, index=True),
            Column('figure_regression', String(256)),
            Column('figure_regression_small', String(256)),
            Column('pvalue_regression_male', Float()),
            Column('pvalue_regression_female', Float()),
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

    def save_regression(self, r):
        try:
            insert = self.regressions. \
                insert().values(r)
            with self.engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            regression_name = r['regression_name']

            del r['regression_name']
            update = self.variable_browser.update().values(r).where(
                self.variable_browser.c.regression_name == regression_name
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

    def search_measures(self, instrument_name=None, keyword=None):

        query_params = []

        if keyword:
            keyword = '%{}%'.format(
                keyword.replace('%', r'\%')
                       .replace('_', r'\_'))
            if not instrument_name:
                query_params.append(
                    self.variable_browser.c.instrument_name.like(
                        keyword, escape='\\'))
            query_params.append(
                self.variable_browser.c.measure_id.like(
                    keyword, escape='\\'))
            query_params.append(
                self.variable_browser.c.measure_name.like(
                    keyword, escape='\\'))
            query_params.append(
                self.variable_browser.c.description.like(
                    keyword, escape='\\'))
            query = self.variable_browser.select(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name)

        df = pd.read_sql(query, self.engine)
        return df

    @property
    def has_descriptions(self):
        with self.engine.connect() as connection:
            return bool(connection.execute(
                        select([func.count()]).
                        select_from(self.variable_browser).
                        where(Column('description').isnot(None)))
                        .scalar())
