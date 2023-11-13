from __future__ import annotations

from typing import Dict, Iterator, Optional, Any, cast

from box import Box

from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Float, Enum, \
    ForeignKey, or_, func
from sqlalchemy.sql import select
from sqlalchemy.sql.schema import UniqueConstraint, PrimaryKeyConstraint

import pandas as pd

from dae.variants.attributes import Sex, Status, Role
from dae.pheno.common import MeasureType


class DbManager:
    """Class that manages access to phenotype databases."""

    STREAMING_CHUNK_SIZE = 25

    def __init__(
        self, dbfile: str, browser_dbfile: Optional[str] = None
    ) -> None:
        self.pheno_dbfile = dbfile
        self.pheno_metadata = MetaData()
        self.variable_browser: Table
        self.regressions: Table
        self.regression_values: Table
        self.family: Table
        self.person: Table
        self.measure: Table
        self.value_continuous: Table
        self.value_ordinal: Table
        self.value_categorical: Table
        self.value_other: Table
        if self.pheno_dbfile == "memory":
            self.pheno_engine = create_engine("sqlite://")
        else:
            self.pheno_engine = create_engine(f"sqlite:///{dbfile}")

        self.update_browser_dbfile(browser_dbfile)

    def has_browser_dbfile(self) -> bool:
        return self.browser_dbfile is not None

    def update_browser_dbfile(self, browser_dbfile: Optional[str]) -> None:
        self.browser_dbfile = browser_dbfile
        self.browser_metadata: Optional[MetaData] = None
        self.browser_engine: Any = None
        if browser_dbfile is not None:
            self.browser_metadata = MetaData()
            self.browser_engine = create_engine(f"sqlite:///{browser_dbfile}")

    def build_browser(self) -> None:
        if self.has_browser_dbfile():
            assert self.browser_metadata is not None
            self._build_browser_tables()
            self.browser_metadata.create_all(self.browser_engine)

    def build(self) -> None:
        """Construct all needed table connections."""
        self._build_person_tables()
        self._build_measure_tables()
        self._build_value_tables()

        self.pheno_metadata.create_all(self.pheno_engine)

        self.build_browser()

    def _build_browser_tables(self) -> None:
        assert self.browser_metadata is not None

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

    def _build_person_tables(self) -> None:
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

    def _build_measure_tables(self) -> None:
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

    def _build_value_tables(self) -> None:
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

    def save(self, v: Dict[str, Optional[str]]) -> None:
        """Save measure values into the database."""
        try:
            insert = self.variable_browser.insert().values(**v)
            with self.browser_engine.begin() as connection:
                connection.execute(insert)
        except Exception:  # pylint: disable=broad-except
            measure_id = v["measure_id"]

            del v["measure_id"]
            update = (
                self.variable_browser.update()
                .values(**v)
                .where(self.variable_browser.c.measure_id == measure_id)
            )
            with self.browser_engine.begin() as connection:
                connection.execute(update)
                connection.commit()

    def save_regression(self, reg: Dict[str, str]) -> None:
        """Save regressions into the database."""
        try:
            insert = self.regressions.insert().values(reg)
            with self.browser_engine.begin() as connection:
                connection.execute(insert)
        except Exception:  # pylint: disable=broad-except
            regression_id = reg["regression_id"]
            del reg["regression_id"]
            update = (
                self.regressions.update()
                .values(reg)
                .where(self.regressions.c.regression_id == regression_id)
            )
            with self.browser_engine.begin() as connection:
                connection.execute(update)
                connection.commit()

    def save_regression_values(self, reg: Dict[str, str]) -> None:
        """Save regression values into the databases."""
        try:
            insert = self.regression_values.insert().values(reg)
            with self.browser_engine.begin() as connection:
                connection.execute(insert)
        except Exception:  # pylint: disable=broad-except
            regression_id = reg["regression_id"]
            measure_id = reg["measure_id"]

            del reg["regression_id"]
            del reg["measure_id"]
            update = (
                self.regression_values.update()
                .values(reg)
                .where(
                    (self.regression_values.c.regression_id == regression_id)
                    & (self.regression_values.c.measure_id == measure_id)
                )
            )
            with self.browser_engine.begin() as connection:
                connection.execute(update)
                connection.commit()

    def get_browser_measure(self, measure_id: str) -> Optional[dict]:
        """Get measrue description from phenotype browser database."""
        sel = select(self.variable_browser)
        sel = sel.where(self.variable_browser.c.measure_id == measure_id)
        with self.browser_engine.connect() as connection:
            vs = connection.execute(sel).fetchall()
            if vs:
                return Box(cast(dict, vs[0]._asdict()))
            return None

    def search_measures(
        self, instrument_name: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Iterator[dict[str, Any]]:
        """Find measert by keyword search."""
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
            query = self.variable_browser.select().where((or_(*query_params)))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name
            )

        with self.browser_engine.connect() as connection:
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

    def search_measures_df(
        self, instrument_name: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> pd.DataFrame:
        """Find measures and return a dataframe with values."""
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
            query = self.variable_browser.select().where(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name
            )

        df = pd.read_sql(query, self.browser_engine)
        return df

    def get_regression(self, regression_id: str) -> Any:
        """Return regressions."""
        selector = select(self.regressions)
        selector = selector.where(
            self.regressions.c.regression_id == regression_id)
        with self.browser_engine.connect() as connection:
            vs = connection.execute(selector).fetchall()
            if vs:
                return vs[0]._mapping  # pylint: disable=protected-access
            return None

    def get_regression_values(self, measure_id: str) -> list[Box]:
        selector = select(self.regression_values)
        selector = selector.where(
            self.regression_values.c.measure_id == measure_id)
        with self.browser_engine.connect() as connection:
            return [
                Box(r._asdict())
                for r in connection.execute(selector).fetchall()
            ]

    @property
    def regression_ids(self) -> list[str]:
        selector = select(self.regressions.c.regression_id)
        with self.browser_engine.connect() as connection:
            return list(map(
                lambda x: x[0],  # type: ignore
                connection.execute(selector)))

    @property
    def regression_display_names(self) -> Dict[str, str]:
        """Return regressions display name."""
        res = {}
        selector = select(
            self.regressions.c.regression_id, self.regressions.c.display_name
        )
        with self.browser_engine.connect() as connection:
            for row in connection.execute(selector):
                res[row[0]] = row[1]
        return res

    @property
    def regression_display_names_with_ids(self) -> dict[str, Any]:
        """Return regression display names with measure IDs."""
        res = {}
        selector = select(
            self.regressions.c.regression_id,
            self.regressions.c.display_name,
            self.regressions.c.instrument_name,
            self.regressions.c.measure_name,
        )
        with self.browser_engine.connect() as connection:
            for row in connection.execute(selector):
                res[row[0]] = {
                    "display_name": row[1],
                    "instrument_name": row[2],
                    "measure_name": row[3],
                }
        return res

    @property
    def has_descriptions(self) -> bool:
        """Check if the database has a description data."""
        with self.browser_engine.connect() as connection:
            return bool(
                connection.execute(
                    select(func.count())  # pylint: disable=not-callable
                    .select_from(self.variable_browser)
                    .where(Column("description").isnot(None))  # type: ignore
                ).scalar()
            )

    def get_value_table(
        self, value_type: MeasureType
    ) -> Table:
        """Return the appropriate table for values based on the value type."""
        if isinstance(value_type, str):
            value_type = MeasureType.from_str(value_type)

        if value_type == MeasureType.continuous:
            return self.value_continuous
        if value_type == MeasureType.ordinal:
            return self.value_ordinal
        if value_type == MeasureType.categorical:
            return self.value_categorical
        if value_type in {MeasureType.raw, MeasureType.text}:
            return self.value_other

        raise ValueError(f"unsupported value type: {value_type}")

    def get_families(self) -> dict:
        """Return families in the phenotype database."""
        value_type = select(self.family)
        with self.pheno_engine.connect() as connection:
            families = connection.execute(value_type).fetchall()
        return {f.family_id: f for f in families}

    def get_persons(self) -> dict:
        """Return individuals in the phenotype database."""
        selector = select(
            self.person.c.id,
            self.person.c.person_id,
            self.family.c.family_id,
            self.person.c.role,
            self.person.c.status,
            self.person.c.sex,
        )
        selector = selector.select_from(self.person.join(self.family))
        with self.pheno_engine.connect() as connection:
            persons = connection.execute(selector).fetchall()
        return {p.person_id: p for p in persons}

    def get_measures(self) -> dict:
        """Return measures in the phenotype database."""
        selector = select(
            self.measure.c.id,
            self.measure.c.measure_id,
            self.measure.c.instrument_name,
            self.measure.c.measure_name,
            self.measure.c.measure_type,
        )
        selector = selector.select_from(self.measure)
        with self.pheno_engine.begin() as connection:
            measures = connection.execute(selector).fetchall()
        return {m.measure_id: m for m in measures}
