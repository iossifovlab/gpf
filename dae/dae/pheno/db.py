"""
Created on Jul 24, 2017

@author: lubo
"""
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Float, Enum, \
    ForeignKey, or_, func
from sqlalchemy.sql import select
import pandas as pd

from dae.variants.attributes import Sex, Status, Role
from dae.pheno.common import MeasureType
from sqlalchemy.sql.schema import UniqueConstraint, PrimaryKeyConstraint


class DbManager(object):
    STREAMING_CHUNK_SIZE = 25

    def __init__(self, dbfile, browser_dbfile=None):
        self.pheno_dbfile = dbfile
        self.pheno_metadata = MetaData()
        if self.pheno_dbfile == "memory":
            self.pheno_engine = create_engine("sqlite://")
        else:
            self.pheno_engine = create_engine(f"sqlite:///{dbfile}")

        self.update_browser_dbfile(browser_dbfile)

    def has_browser_dbfile(self):
        return self.browser_dbfile is not None

    def update_browser_dbfile(self, browser_dbfile):
        self.browser_dbfile = browser_dbfile
        if browser_dbfile is not None:
            self.browser_metadata = MetaData()
            self.browser_engine = create_engine(f"sqlite:///{browser_dbfile}")
        else:
            self.browser_metadata = None
            self.browser_engine = None

    def build_browser(self):
        if self.has_browser_dbfile():
            self._build_browser_tables()
            self.browser_metadata.create_all(self.browser_engine)

    def build(self):
        self._build_person_tables()
        self._build_measure_tables()
        self._build_value_tables()

        self.pheno_metadata.create_all(self.pheno_engine)

        self.build_browser()

    def _build_browser_tables(self):
        self.variable_browser = Table(
            "variable_browser",
            self.browser_metadata,
            Column(
                "measure_id",
                String(128),
                nullable=False,
                index=True,
                unique=True,
                primary_key=True,
            ),
            Column("instrument_name", String(64), nullable=False, index=True),
            Column("measure_name", String(64), nullable=False, index=True),
            Column("measure_type", Enum(MeasureType), nullable=False),
            Column("description", String(256)),
            Column("values_domain", String(256)),
            Column("figure_distribution_small", String(256)),
            Column("figure_distribution", String(256)),
        )

        self.regressions = Table(
            "regressions",
            self.browser_metadata,
            Column(
                "regression_id",
                String(128),
                nullable=False,
                index=True,
                primary_key=True,
            ),
            Column("instrument_name", String(128)),
            Column("measure_name", String(128), nullable=False),
            Column("display_name", String(256)),
        )

        self.regression_values = Table(
            "regression_values",
            self.browser_metadata,
            Column("regression_id", String(128), nullable=False, index=True),
            Column("measure_id", String(128), nullable=False, index=True),
            Column("figure_regression", String(256)),
            Column("figure_regression_small", String(256)),
            Column("pvalue_regression_male", Float()),
            Column("pvalue_regression_female", Float()),
            PrimaryKeyConstraint(
                "regression_id", "measure_id", name="regression_pkey"
            ),
        )

    def _build_person_tables(self):
        self.family = Table(
            "family",
            self.pheno_metadata,
            Column("id", Integer(), primary_key=True),
            Column(
                "family_id",
                String(64),
                nullable=False,
                unique=True,
                index=True,
            ),
        )
        self.person = Table(
            "person",
            self.pheno_metadata,
            Column("id", Integer(), primary_key=True),
            Column("family_id", ForeignKey("family.id")),
            Column("person_id", String(16), nullable=False, index=True),
            Column("role", Enum(Role), nullable=False),
            Column(
                "status",
                Enum(Status),
                nullable=False,
                default=Status.unaffected,
            ),
            Column("sex", Enum(Sex), nullable=False),
            Column("sample_id", String(16), nullable=True),
            UniqueConstraint("family_id", "person_id", name="person_key"),
        )

    def _build_measure_tables(self):
        self.measure = Table(
            "measure",
            self.pheno_metadata,
            Column("id", Integer(), primary_key=True),
            Column(
                "measure_id",
                String(128),
                nullable=False,
                index=True,
                unique=True,
            ),
            Column("instrument_name", String(64), nullable=False, index=True),
            Column("measure_name", String(64), nullable=False, index=True),
            Column("description", String(255)),
            Column("measure_type", Enum(MeasureType), index=True),
            Column("individuals", Integer()),
            Column("default_filter", String(255)),
            Column("min_value", Float(), nullable=True),
            Column("max_value", Float(), nullable=True),
            Column("values_domain", String(255), nullable=True),
            Column("rank", Integer(), nullable=True),
            UniqueConstraint(
                "instrument_name", "measure_name", name="measure_key"
            ),
        )

    def _build_value_tables(self):
        self.value_continuous = Table(
            "value_continuous",
            self.pheno_metadata,
            Column("person_id", ForeignKey("person.id")),
            Column("measure_id", ForeignKey("measure.id")),
            Column("value", Float(), nullable=False),
            PrimaryKeyConstraint("person_id", "measure_id"),
        )
        self.value_ordinal = Table(
            "value_ordinal",
            self.pheno_metadata,
            Column("person_id", ForeignKey("person.id")),
            Column("measure_id", ForeignKey("measure.id")),
            Column("value", Float(), nullable=False),
            PrimaryKeyConstraint("person_id", "measure_id"),
        )
        self.value_categorical = Table(
            "value_categorical",
            self.pheno_metadata,
            Column("person_id", ForeignKey("person.id")),
            Column("measure_id", ForeignKey("measure.id")),
            Column("value", String(127), nullable=False),
            PrimaryKeyConstraint("person_id", "measure_id"),
        )
        self.value_other = Table(
            "value_other",
            self.pheno_metadata,
            Column("person_id", ForeignKey("person.id")),
            Column("measure_id", ForeignKey("measure.id")),
            Column("value", String(127), nullable=False),
            PrimaryKeyConstraint("person_id", "measure_id"),
        )

    def save(self, v):
        try:
            insert = self.variable_browser.insert().values(**v)
            with self.browser_engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            # traceback.print_exc()
            measure_id = v["measure_id"]

            del v["measure_id"]
            update = (
                self.variable_browser.update()
                .values(**v)
                .where(self.variable_browser.c.measure_id == measure_id)
            )
            with self.browser_engine.begin() as connection:
                connection.execute(update)

    def save_regression(self, r):
        try:
            insert = self.regressions.insert().values(r)
            with self.browser_engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            regression_id = r["regression_id"]
            del r["regression_id"]
            update = (
                self.regressions.update()
                .values(r)
                .where(self.regressions.c.regression_id == regression_id)
            )
            with self.browser_engine.begin() as connection:
                connection.execute(update)

    def save_regression_values(self, r):
        try:
            insert = self.regression_values.insert().values(r)
            with self.browser_engine.begin() as connection:
                connection.execute(insert)
        except Exception:
            regression_id = r["regression_id"]
            measure_id = r["measure_id"]

            del r["regression_id"]
            del r["measure_id"]
            update = (
                self.regression_values.update()
                .values(r)
                .where(
                    (self.regression_values.c.regression_id == regression_id)
                    & (self.regression_values.c.measure_id == measure_id)
                )
            )
            with self.browser_engine.begin() as connection:
                connection.execute(update)

    def get_browser(self, measure_id):
        s = select([self.variable_browser])
        s = s.where(self.variable_browser.c.measure_id == measure_id)
        with self.browser_engine.connect() as connection:
            vs = connection.execute(s).fetchall()
            if vs:
                return vs[0]
            else:
                return None

    def search_measures(self, instrument_name=None, keyword=None):

        query_params = []

        if keyword:
            keyword = "%{}%".format(
                keyword.replace("%", r"\%").replace("_", r"\_")
            )
            if not instrument_name:
                query_params.append(
                    self.variable_browser.c.instrument_name.like(
                        keyword, escape="\\"
                    )
                )
            query_params.append(
                self.variable_browser.c.measure_id.like(keyword, escape="\\")
            )
            query_params.append(
                self.variable_browser.c.measure_name.like(keyword, escape="\\")
            )
            query_params.append(
                self.variable_browser.c.description.like(keyword, escape="\\")
            )
            query = self.variable_browser.select(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name
            )

        with self.browser_engine.connect() as connection:
            print(query)
            cursor = connection.execution_options(stream_results=True)\
                .execute(query)
            rows = cursor.fetchmany(self.STREAMING_CHUNK_SIZE)
            while rows:
                for row in rows:
                    yield {
                        "measure_id": row[0],
                        "instrument_name": row[1],
                        "measure_name": row[2],
                        "measure_type": row[3],
                        "description": row[4],
                        "values_domain": row[5],
                        "figure_distribution_small": row[6],
                        "figure_distribution": row[7],
                    }
                rows = cursor.fetchmany(self.STREAMING_CHUNK_SIZE)

    def search_measures_df(self, instrument_name=None, keyword=None):

        query_params = []

        if keyword:
            keyword = "%{}%".format(
                keyword.replace("%", r"\%").replace("_", r"\_")
            )
            if not instrument_name:
                query_params.append(
                    self.variable_browser.c.instrument_name.like(
                        keyword, escape="\\"
                    )
                )
            query_params.append(
                self.variable_browser.c.measure_id.like(keyword, escape="\\")
            )
            query_params.append(
                self.variable_browser.c.measure_name.like(keyword, escape="\\")
            )
            query_params.append(
                self.variable_browser.c.description.like(keyword, escape="\\")
            )
            query = self.variable_browser.select(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name
            )

        df = pd.read_sql(query, self.browser_engine)
        return df

    def get_regression(self, regression_id):
        s = select([self.regressions])
        s = s.where(self.regressions.c.regression_id == regression_id)
        with self.browser_engine.connect() as connection:
            vs = connection.execute(s).fetchall()
            if vs:
                return vs[0]
            else:
                return None

    def get_regression_values(self, measure_id):
        s = select([self.regression_values])
        s = s.where(self.regression_values.c.measure_id == measure_id)
        with self.browser_engine.connect() as connection:
            return connection.execute(s).fetchall()

    @property
    def regression_ids(self):
        s = select([self.regressions.c.regression_id])
        with self.browser_engine.connect() as connection:
            return list(map(lambda x: x.values()[0], connection.execute(s)))

    @property
    def regression_display_names(self):
        res = {}
        s = select(
            [self.regressions.c.regression_id, self.regressions.c.display_name]
        )
        with self.browser_engine.connect() as connection:
            for row in connection.execute(s):
                res[row.values()[0]] = row.values()[1]
        return res

    @property
    def regression_display_names_with_ids(self):
        res = {}
        s = select(
            [
                self.regressions.c.regression_id,
                self.regressions.c.display_name,
                self.regressions.c.instrument_name,
                self.regressions.c.measure_name,
            ]
        )
        with self.browser_engine.connect() as connection:
            for row in connection.execute(s):
                res[row.values()[0]] = {
                    "display_name": row.values()[1],
                    "instrument_name": row.values()[2],
                    "measure_name": row.values()[3],
                }
        return res

    @property
    def has_descriptions(self):
        with self.browser_engine.connect() as connection:
            return bool(
                connection.execute(
                    select([func.count()])
                    .select_from(self.variable_browser)
                    .where(Column("description").isnot(None))
                ).scalar()
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
        with self.pheno_engine.connect() as connection:
            families = connection.execute(s).fetchall()
        families = {f.family_id: f for f in families}
        return families

    def get_persons(self):
        s = select(
            [
                self.person.c.id,
                self.person.c.person_id,
                self.family.c.family_id,
                self.person.c.role,
                self.person.c.status,
                self.person.c.sex,
            ]
        )
        s = s.select_from(self.person.join(self.family))
        with self.pheno_engine.connect() as connection:
            persons = connection.execute(s).fetchall()
        persons = {p.person_id: p for p in persons}
        return persons

    def get_measures(self):
        s = select(
            [
                self.measure.c.id,
                self.measure.c.measure_id,
                self.measure.c.instrument_name,
                self.measure.c.measure_name,
                self.measure.c.measure_type,
            ]
        )
        s = s.select_from(self.measure)
        with self.pheno_engine.begin() as connection:
            measures = connection.execute(s).fetchall()
        measures = {m.measure_id: m for m in measures}
        return measures
