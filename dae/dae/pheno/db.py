from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, Dict, cast

import pandas as pd
from box import Box
from sqlalchemy import (
    Column,
    Double,
    Float,
    Integer,
    MetaData,
    Select,
    String,
    Table,
    create_engine,
    func,
    or_,
)
from sqlalchemy.sql import select
from sqlalchemy.sql.schema import PrimaryKeyConstraint, UniqueConstraint

from dae.pheno.common import MeasureType
from dae.variants.attributes import Status


class PhenoDb:  # pylint: disable=too-many-instance-attributes
    """Class that manages access to phenotype databases."""

    STREAMING_CHUNK_SIZE = 25

    def __init__(
            self, dbfile: str, read_only: bool = True,
    ) -> None:
        # self.verify_pheno_folder(folder)
        self.dbfile = dbfile
        self.engine = create_engine(
            f"duckdb:///{dbfile}", connect_args={"read_only": read_only},
        )
        self.pheno_metadata = MetaData()
        self.variable_browser: Table
        self.regressions: Table
        self.regression_values: Table
        self.family: Table
        self.person: Table
        self.measure: Table
        self.instrument: Table
        self.instrument_values_tables: dict[str, Table] = {}

    @staticmethod
    def verify_pheno_folder(folder: Path) -> None:
        """Verify integrity of a pheno db folder."""
        parquet_folder = folder / "parquet"
        assert parquet_folder.exists()
        family_file = parquet_folder / "family.parquet"
        assert family_file.exists()
        person_file = parquet_folder / "person.parquet"
        assert person_file.exists()
        instrument_file = parquet_folder / "instrument.parquet"
        assert instrument_file.exists()
        measure_file = parquet_folder / "measure.parquet"
        assert measure_file.exists()
        instruments_dir = parquet_folder / "instruments"
        assert instruments_dir.exists()
        assert instruments_dir.is_dir()
        assert len(list(instruments_dir.glob("*"))) > 0

    def build_browser(self) -> None:
        self._build_browser_tables()

    def build(self, create: bool = False) -> None:
        """Construct all needed table connections."""
        self._build_person_tables()
        self.build_instruments_and_measures_table()
        if create:
            self.pheno_metadata.create_all(self.engine)
        self.build_instrument_values_tables()

        self.build_browser()

        if create:
            self.pheno_metadata.create_all(self.engine)

    def create_all_tables(self) -> None:
        self.pheno_metadata.create_all(self.engine)

    def build_instruments_and_measures_table(self) -> None:
        """Create tables for instruments and measures."""
        if getattr(self, "instruments", None) is None:
            self.instrument = Table(
                "instrument",
                self.pheno_metadata,
                Column(
                    "instrument_name", String(64), nullable=False, index=True,
                ),
                Column("table_name", String(64), nullable=False),
            )

        if getattr(self, "measure", None) is None:
            self.measure = Table(
                "measure",
                self.pheno_metadata,
                Column(
                    "measure_id",
                    String(128),
                    nullable=False,
                    index=True,
                    unique=True,
                ),
                Column(
                    "db_column_name",
                    String(128),
                    nullable=False,
                ),
                Column("measure_name", String(64), nullable=False, index=True),
                Column("instrument_name", String(64), nullable=False),
                Column("description", String(255)),
                Column("measure_type", Integer(), index=True),
                Column("individuals", Integer()),
                Column("default_filter", String(255)),
                Column("min_value", Float(), nullable=True),
                Column("max_value", Float(), nullable=True),
                Column("values_domain", String(255), nullable=True),
                Column("rank", Integer(), nullable=True),
            )

    def build_instrument_values_tables(self) -> None:
        """
        Create instrument values tables.

        Each row is basically a list of every measure value in the instrument
        for a certain person.
        """
        query = select(
            self.instrument.c.instrument_name,
            self.instrument.c.table_name,
        )
        with self.engine.connect() as connection:
            instruments_rows = connection.execute(query)
            instrument_table_names = {}
            instrument_measures: dict[str, list[str]] = {}
            for row in instruments_rows:
                instrument_table_names[row.instrument_name] = row.table_name
                instrument_measures[row.instrument_name] = []

        query = select(
            self.measure.c.measure_id,
            self.measure.c.measure_type,
            self.measure.c.db_column_name,
            self.instrument.c.instrument_name,
        ).join(
            self.instrument,
            self.measure.c.instrument_name == self.instrument.c.instrument_name,
        )
        with self.engine.connect() as connection:
            results = connection.execute(query)
            measure_columns = {}
            for result_row in results:
                instrument_measures[result_row.instrument_name].append(
                    result_row.measure_id,
                )
                if MeasureType.is_numeric(result_row.measure_type):
                    column_type: Float | String = Float()
                else:
                    column_type = String(127)
                measure_columns[result_row.measure_id] = \
                    Column(
                        f"{result_row.db_column_name}",
                        column_type, nullable=True,
                )

        for instrument_name, table_name in instrument_table_names.items():
            cols = [
                measure_columns[m_id]
                for m_id in
                instrument_measures[instrument_name]
            ]

            if instrument_name not in self.instrument_values_tables:
                self.instrument_values_tables[instrument_name] = Table(
                    table_name,
                    self.pheno_metadata,
                    Column(
                        "person_id",
                        String(16),
                        nullable=False,
                        index=True,
                        unique=True,
                        primary_key=True,
                    ),
                    Column(
                        "family_id", String(64), nullable=False, index=True,
                    ),
                    Column("role", String(64), nullable=False, index=True),
                    Column(
                        "status",
                        Integer(),
                        nullable=False,
                        default=Status.unaffected,
                    ),
                    Column("sex", Integer(), nullable=False),
                    *cols,
                    extend_existing=True,
                )

    def _split_measures_into_groups(
        self, measure_ids: list[str], group_size: int = 60,
    ) -> list[list[str]]:
        groups_count = int(len(measure_ids) / group_size) + 1
        if (groups_count) == 1:
            return [measure_ids]
        measure_groups = []
        for i in range(groups_count):
            begin = i * group_size
            end = (i + 1) * group_size
            group = measure_ids[begin:end]
            if len(group) > 0:
                measure_groups.append(group)
        return measure_groups

    def clear_instruments_table(self, drop: bool = False) -> None:
        """Clear the instruments table."""
        if getattr(self, "instruments", None) is None:
            return
        with self.engine.begin() as connection:
            connection.execute(self.instrument.delete())
            if drop:
                self.instrument.drop(connection, checkfirst=False)
            connection.commit()

    def clear_measures_table(self, drop: bool = False) -> None:
        """Clear the measures table."""
        if getattr(self, "measures", None) is None:
            return
        with self.engine.begin() as connection:
            connection.execute(self.measure.delete())
            if drop:
                self.measure.drop(connection, checkfirst=False)
            connection.commit()

    def clear_instrument_values_tables(self, drop: bool = False) -> None:
        """Clear all instrument values tables."""
        if getattr(self, "instrument_values_tables", None) is None:
            return
        with self.engine.begin() as connection:
            for instrument_table in self.instrument_values_tables.values():
                connection.execute(instrument_table.delete())
                if drop:
                    instrument_table.drop(connection, checkfirst=False)
            connection.commit()

    def get_instrument_column_names(self) -> dict[str, list[str]]:
        """Return a map of instruments and their measure column names."""
        query = select(
            self.measure.c.db_column_name,
            self.instrument.c.instrument_name,
        ).join(self.instrument)
        with self.engine.connect() as connection:
            results = connection.execute(query)

        instrument_col_names = {}
        for result_row in results:
            if result_row.instrument_name not in instrument_col_names:
                instrument_col_names[result_row.instrument_name] = [
                    result_row.db_column_name,
                ]
            else:
                instrument_col_names[result_row.instrument_name].append(
                    result_row.db_column_name,
                )
        return instrument_col_names

    def get_measure_column_names(
        self, measure_ids: list[str] | None = None,
    ) -> dict[str, str]:
        """Return measure column names mapped to their measure IDs."""
        query = select(
            self.measure.c.measure_id,
            self.measure.c.db_column_name,
        )
        if measure_ids is not None:
            query = query.where(self.measure.c.measure_id.in_(measure_ids))
        with self.engine.connect() as connection:
            results = connection.execute(query)

            measure_column_names = {}
            for result_row in results:
                measure_column_names[result_row.measure_id] = \
                    result_row.db_column_name
        return measure_column_names

    def get_measure_column_names_reverse(
        self, measure_ids: list[str] | None = None,
    ) -> dict[str, str]:
        """Return measure column names mapped to their measure IDs."""
        query = select(
            self.measure.c.measure_id,
            self.measure.c.db_column_name,
        )
        if measure_ids is not None:
            query = query.where(self.measure.c.measure_id.in_(measure_ids))
        with self.engine.connect() as connection:
            results = connection.execute(query)

            measure_column_names = {}
            for result_row in results:
                measure_column_names[result_row.db_column_name] = \
                    result_row.measure_id
        return measure_column_names

    def _build_browser_tables(self) -> None:
        self.variable_browser = Table(
            "variable_browser",
            self.pheno_metadata,
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
            Column("measure_type", Integer(), nullable=False),
            Column("description", String(256)),
            Column("values_domain", String(256)),
            Column("figure_distribution_small", String(256)),
            Column("figure_distribution", String(256)),
        )

        self.regressions = Table(
            "regression",
            self.pheno_metadata,
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
            self.pheno_metadata,
            Column("regression_id", String(128), nullable=False, index=True),
            Column("measure_id", String(128), nullable=False, index=True),
            Column("figure_regression", String(256)),
            Column("figure_regression_small", String(256)),
            Column("pvalue_regression_male", Double()),
            Column("pvalue_regression_female", Double()),
            PrimaryKeyConstraint(
                "regression_id", "measure_id", name="regression_pkey",
            ),
        )

    def _build_person_tables(self) -> None:
        self.family = Table(
            "family",
            self.pheno_metadata,
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
            Column("family_id", String(64), nullable=False),
            Column("person_id", String(16), nullable=False, index=True),
            Column("role", Integer(), nullable=False),
            Column(
                "status",
                Integer(),
                nullable=False,
                default=Status.unaffected,
            ),
            Column("sex", Integer(), nullable=False),
            Column("sample_id", String(16), nullable=True),
            UniqueConstraint("family_id", "person_id", name="person_key"),
        )

    def save(self, v: Dict[str, str | None]) -> None:
        """Save measure values into the database."""
        try:
            insert = self.variable_browser.insert().values(**v)
            with self.engine.begin() as connection:
                connection.execute(insert)
                connection.commit()
        except Exception:  # pylint: disable=broad-except
            measure_id = v["measure_id"]

            delete = (
                self.variable_browser.delete()
                .where(self.variable_browser.c.measure_id == measure_id)
            )
            with self.engine.connect() as connection:
                connection.execute(delete)
                connection.commit()
            with self.engine.connect() as connection:
                connection.execute(insert)
                connection.commit()

    def save_regression(self, reg: Dict[str, str]) -> None:
        """Save regressions into the database."""
        try:
            insert = self.regressions.insert().values(reg)
            with self.engine.begin() as connection:
                connection.execute(insert)
        except Exception:  # pylint: disable=broad-except
            regression_id = reg["regression_id"]
            del reg["regression_id"]
            update = (
                self.regressions.update()
                .values(reg)
                .where(self.regressions.c.regression_id == regression_id)
            )
            with self.engine.begin() as connection:
                connection.execute(update)
                connection.commit()

    def save_regression_values(self, reg: Dict[str, str]) -> None:
        """Save regression values into the databases."""
        try:
            insert = self.regression_values.insert().values(reg)
            with self.engine.begin() as connection:
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
                    & (self.regression_values.c.measure_id == measure_id),
                )
            )
            with self.engine.begin() as connection:
                connection.execute(update)
                connection.commit()

    def get_browser_measure(self, measure_id: str) -> dict | None:
        """Get measure description from phenotype browser database."""
        sel = select(self.variable_browser)
        sel = sel.where(self.variable_browser.c.measure_id == measure_id)
        with self.engine.connect() as connection:
            vs = connection.execute(sel).fetchall()
            if vs:
                return Box(cast(dict, vs[0]._asdict()))
            return None

    def build_measures_query(
        self, instrument_name: str | None = None,
        keyword: str | None = None,
    ) -> Select[Any]:
        """Find measures by keyword search."""
        query_params = []

        if keyword:
            keyword = keyword.replace("%", r"/%").replace("_", r"/_")
            keyword = f"%{keyword}%"
            if not instrument_name:
                query_params.append(
                    self.variable_browser.c.instrument_name.ilike(
                        keyword, escape="/",
                    ),
                )
            query_params.extend(
                (self.variable_browser.c.measure_id.ilike(keyword, escape="/"),
                self.variable_browser.c.measure_name.ilike(keyword, escape="/"),
                self.variable_browser.c.description.ilike(keyword, escape="/")),
            )
            query = self.variable_browser.select().where(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name,
            )
        return query.order_by(
            self.variable_browser.c.instrument_name,
            self.variable_browser.c.measure_id,
        )

    def search_measures(
        self, instrument_name: str | None = None,
        keyword: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Find measures by keyword search."""
        query = self.build_measures_query(instrument_name, keyword)

        with self.engine.connect() as connection:
            cursor = connection.execution_options(stream_results=True)\
                .execute(query)
            rows = cursor.fetchmany(self.STREAMING_CHUNK_SIZE)
            while rows:
                for row in rows:
                    yield {
                        "measure_id": row[0],
                        "instrument_name": row[1],
                        "measure_name": row[2],
                        "measure_type": MeasureType(row[3]),
                        "description": row[4],
                        "values_domain": row[5],
                        "figure_distribution_small": row[6],
                        "figure_distribution": row[7],
                    }
                rows = cursor.fetchmany(self.STREAMING_CHUNK_SIZE)

    def search_measures_df(
        self, instrument_name: str | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        """Find measures and return a dataframe with values."""
        query = self.build_measures_query(instrument_name, keyword)

        df = pd.read_sql(query, self.engine)
        return df

    def get_regression(self, regression_id: str) -> Any:
        """Return regressions."""
        selector = select(self.regressions)
        selector = selector.where(
            self.regressions.c.regression_id == regression_id)
        with self.engine.connect() as connection:
            vs = connection.execute(selector).fetchall()
            if vs:
                return vs[0]._mapping  # pylint: disable=protected-access
            return None

    def get_regression_values(self, measure_id: str) -> list[Box]:
        selector = select(self.regression_values)
        selector = selector.where(
            self.regression_values.c.measure_id == measure_id)
        with self.engine.connect() as connection:
            return [
                Box(r._asdict())
                for r in connection.execute(selector).fetchall()
            ]

    @property
    def regression_ids(self) -> list[str]:
        selector = select(self.regressions.c.regression_id)
        with self.engine.connect() as connection:
            return list(map(
                lambda x: x[0],
                connection.execute(selector)))

    @property
    def regression_display_names(self) -> Dict[str, str]:
        """Return regressions display name."""
        res = {}
        selector = select(
            self.regressions.c.regression_id, self.regressions.c.display_name,
        )
        with self.engine.connect() as connection:
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
        with self.engine.connect() as connection:
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
        with self.engine.connect() as connection:
            return bool(
                connection.execute(
                    select(func.count())  # pylint: disable=not-callable
                    .select_from(self.variable_browser)
                    .where(Column("description").isnot(None)),
                ).scalar(),
            )

    def get_families(self) -> dict:
        """Return families in the phenotype database."""
        value_type = select(self.family)
        with self.engine.connect() as connection:
            families = connection.execute(value_type).fetchall()
        return {f.family_id: f for f in families}

    def get_persons(self) -> dict:
        """Return individuals in the phenotype database."""
        selector = select(
            self.person.c.person_id,
            self.person.c.family_id,
            self.person.c.role,
            self.person.c.status,
            self.person.c.sex,
        )
        with self.engine.connect() as connection:
            persons = connection.execute(selector).fetchall()
        return {p.person_id: p for p in persons}

    def get_measures(self) -> dict:
        """Return measures in the phenotype database."""
        selector = select(
            self.measure.c.measure_id,
            self.measure.c.instrument_name,
            self.measure.c.measure_name,
            self.measure.c.measure_type,
        )
        selector = selector.select_from(self.measure)
        with self.engine.begin() as connection:
            measures = connection.execute(selector).fetchall()
        return {m.measure_id: m for m in measures}


def safe_db_name(name: str) -> str:
    name = name.replace(".", "_").replace("-", "_").replace(" ", "_").lower()
    name = name.replace("/", "_")
    if name[0].isdigit():
        name = f"_{name}"
    return name


def generate_instrument_table_name(instrument_name: str) -> str:
    instrument_name = safe_db_name(instrument_name)
    return f"{instrument_name}_measure_values"
