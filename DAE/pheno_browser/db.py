'''
Created on Aug 31, 2017

@author: lubo
'''
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, String, Float, Enum, func, or_
from sqlalchemy.sql import select
from sqlalchemy.schema import PrimaryKeyConstraint
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
            Column('regression_id', String(128),
                   nullable=False, index=True, primary_key=True),
            Column('instrument_name', String(128)),
            Column('measure_name', String(128), nullable=False),
            Column('display_name', String(256)),
        )

        self.regression_values = Table(
            'regression_values', self.metadata,
            Column('regression_id', String(128), nullable=False, index=True),
            Column('measure_id', String(128), nullable=False, index=True),
            Column('figure_regression', String(256)),
            Column('figure_regression_small', String(256)),
            Column('pvalue_regression_male', Float()),
            Column('pvalue_regression_female', Float()),
            PrimaryKeyConstraint('regression_id', 'measure_id',
                                 name='regression_pkey')
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
            insert = self.regressions.insert().values(r)
            with self.engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            regression_id = r['regression_id']
            del(r['regression_id'])
            update = self.regressions.update().values(r).where(
                    self.regressions.c.regression_id == regression_id
                )
            with self.engine.begin() as connection:
                connection.execute(update)

    def save_regression_values(self, r):
        try:
            insert = self.regression_values.insert().values(r)
            with self.engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            regression_id = r['regression_id']
            measure_id = r['measure_id']

            del r['regression_id']
            del r['measure_id']
            update = self.regression_values.update().values(r).where(
                (self.regression_values.c.regression_id == regression_id)
                & (self.regression_values.c.measure_id == measure_id)
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

    def get_regression(self, regression_id):
        s = select([self.regressions])
        s = s.where(self.regressions.c.regression_id == regression_id)
        with self.engine.connect() as connection:
            vs = connection.execute(s).fetchall()
            if vs:
                return vs[0]
            else:
                return None

    def get_regression_values(self, measure_id):
        s = select([self.regression_values])
        s = s.where(self.regression_values.c.measure_id == measure_id)
        with self.engine.connect() as connection:
            return connection.execute(s).fetchall()

    @property
    def regression_ids(self):
        s = select([self.regressions.c.regression_id])
        with self.engine.connect() as connection:
            return list(map(lambda x: x.values()[0], connection.execute(s)))

    @property
    def regression_display_names(self):
        res = {}
        s = select([self.regressions.c.regression_id,
                    self.regressions.c.display_name])
        with self.engine.connect() as connection:
            for row in connection.execute(s):
                res[row.values()[0]] = row.values()[1]
        return res

    @property
    def regression_display_names_with_ids(self):
        res = {}
        s = select([self.regressions.c.regression_id,
                    self.regressions.c.display_name,
                    self.regressions.c.instrument_name,
                    self.regressions.c.measure_name])
        with self.engine.connect() as connection:
            for row in connection.execute(s):
                res[row.values()[0]] = {
                    'display_name': row.values()[1],
                    'instrument_name': row.values()[2],
                    'measure_name': row.values()[3]
                }
        return res

    @property
    def has_descriptions(self):
        with self.engine.connect() as connection:
            return bool(connection.execute(
                        select([func.count()]).
                        select_from(self.variable_browser).
                        where(Column('description').isnot(None)))
                        .scalar())
