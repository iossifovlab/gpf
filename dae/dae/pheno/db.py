from __future__ import annotations

from collections.abc import Iterator
from functools import reduce
from pathlib import Path
import textwrap
from typing import Any, Dict, cast

import duckdb
import pandas as pd
import sqlglot
from box import Box
from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    func,
)
from sqlalchemy.sql.schema import PrimaryKeyConstraint, UniqueConstraint
from sqlglot import column, expressions, select, table

from dae.pheno.common import MeasureType
from dae.utils.sql_utils import to_duckdb_transpile
from dae.variants.attributes import Status


class PhenoDb:  # pylint: disable=too-many-instance-attributes
    """Class that manages access to phenotype databases."""

    PAGE_SIZE = 1001

    def __init__(
            self, dbfile: str, read_only: bool = True,
    ) -> None:
        # self.verify_pheno_folder(folder)
        self.dbfile = dbfile
        self.connection = duckdb.connect(f"duckdb:///{dbfile}", read_only=True)
        self.pheno_metadata = MetaData()
        self.variable_browser = table("variable_browser")
        self.regressions = table("regressions")
        self.regression_values = table("regression_values")
        self.family = table("family")
        self.person = table("person")
        self.measure = table("measure")
        self.instrument = table("instrument")
        self.instrument_values_tables = find_instrument_values_tables()

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


    def build(self) -> None:
        """Construct all needed table connections."""
        self._build_person_tables()
        self._build_instruments_and_measures_table()
        self._build_browser()

    def _build_person_tables(self) -> None:
        create_family = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE family(
                family_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
            );
            CREATE UNIQUE INDEX family_family_id_idx
                ON family (family_id);
            """,
        ))

        create_person = sqlglot.parse(textwrap.dedent(
            f"""
            CREATE TABLE person(
                family_id VARCHAR NOT NULL,
                person_id VARCHAR NOT NULL,
                role INT NOT NULL,
                status INT NOT NULL DEFAULT {Status.unaffected.value},
                sex INT NOT NULL,
                sample_id VARCHAR,
                PRIMARY KEY (family_id, person_id)
            );
            CREATE UNIQUE INDEX person_person_id_idx
                ON person (person_id);
            """,
        ))

        queries = [
            *create_family,
            *create_person,
        ]

        with self.connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)

    def _build_instruments_and_measures_table(self) -> None:
        """Create tables for instruments and measures."""
        create_instrument = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE instrument(
                instrument_name VARCHAR NOT NULL PRIMARY KEY,
                table_name VARCHAR NOT NULL,
            );
            CREATE UNIQUE INDEX instrument_instrument_name_idx
                ON instrument (instrument_name);
            """,
        ))

        create_measure = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE measure(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                db_column_name VARCHAR NOT NULL,
                measure_name VARCHAR NOT NULL,
                instrument_name VARCHAR NOT NULL,
                description VARCHAR,
                measure_type INT,
                individuals INT,
                default_filter VARCHAR,
                min_value FLOAT,
                max_value FLOAT,
                values_domain VARCHAR,
                rank INT,
            );
            CREATE UNIQUE INDEX measure_measure_id_idx
                ON measure (measure_id);
            CREATE INDEX measure_measure_name_idx
                ON measure (measure_name);
            CREATE INDEX measure_measure_type_idx
                ON measure (measure_type);
            """,
        ))

        queries = [
            *create_instrument,
            *create_measure,
        ]

        with self.connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)

    def _build_browser(self) -> None:
        create_variable_browser = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE variable_browser(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR NOT NULL,
                measure_name VARCHAR NOT NULL,
                measure_type INT NOT NULL,
                description VARCHAR,
                values_domain VARCHAR,
                figure_distribution_small VARCHAR,
                figure_distribution VARCHAR
            );
            CREATE UNIQUE INDEX variable_browser_measure_id_idx
                ON variable_browser (measure_id);
            CREATE INDEX variable_browser_instrument_name_idx
                ON variable_browser (instrument_name);
            CREATE INDEX variable_browser_measure_name_idx
                ON variable_browser (measure_name);
            """,
        ))

        create_regression = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE regression(
                regression_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR,
                measure_name VARCHAR NOT NULL,
                display_name VARCHAR,
            );
            CREATE UNIQUE INDEX regression_regression_id_idx
                ON regression (regression_id);
            """,
        ))

        create_regression_values = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE regression_values(
                regression_id VARCHAR NOT NULL,
                measure_id VARCHAR NOT NULL,
                figure_regression VARCHAR,
                figure_regression_small VARCHAR,
                pvalue_regression_male DOUBLE,
                pvalue_regression_female DOUBLE,
                PRIMARY KEY (regression_id, measure_id)
            );
            CREATE INDEX regression_values_regression_id_idx
                ON regression_values (regression_id);
            CREATE INDEX regression_values_measure_id_idx
                ON regression_values (measure_id);
            """,
        ))

        queries = [
            *create_variable_browser,
            *create_regression,
            *create_regression_values,
        ]

        with self.connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)

    def find_instrument_values_tables(self) -> dict[str, expressions.Table]:
        """
        Create instrument values tables.

        Each row is basically a list of every measure value in the instrument
        for a certain person.
        """
        query = select(
            "instrument_name",
            "table_name",
        ).from_(self.instrument)

        with self.connection.cursor() as cursor:
            results = cursor.execute(query).fetchall()

        return {i_name: table(t_name) for i_name, t_name in results}

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
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> expressions.Select:
        """Find measures by keyword search."""

        joined_tables = {}
        regression_ids = self.regression_ids

        query = select(
            column("measure_id", self.variable_browser.alias_or_name),
            column("instrument_name", self.variable_browser.alias_or_name),
            column("measure_name", self.variable_browser.alias_or_name),
            column("measure_type", self.variable_browser.alias_or_name),
            column("description", self.variable_browser.alias_or_name),
            column("values_domain", self.variable_browser.alias_or_name),
            column(
                "figure_distribution_small",
                self.variable_browser.alias_or_name,
            ),
            column("figure_distribution", self.variable_browser.alias_or_name),
        ).from_(self.variable_browser)

        for regression_id in regression_ids:
            reg_table = table("regression_values").as_(regression_id)
            query = query.join(
                "regression_values",
                on=sqlglot.condition(
                    "variable_browser.measure_id = table.measure_id and"
                    f"table.regression_id = {regression_id}",
                ),
                join_type="LEFT OUTER",
            )
            joined_tables[regression_id] = reg_table
            query.select(
                column(
                    "pvalue_regression_male", table=reg_table.alias_or_name,
                ).as_(f"{regression_id}_pvalue_regression_male"),
                column(
                    "pvalue_regression_female", table=reg_table.alias_or_name,
                ).as_(f"{regression_id}_pvalue_regression_female"),
            )

        query = query.distinct()

        if keyword:
            column_filters = []
            keyword = keyword.replace("%", r"/%").replace("_", r"/_")
            keyword = f"%{keyword}%"
            if not instrument_name:
                column_filters.append(
                    column(
                        "instrument_name",
                        table="variable_browser",
                    ).like(keyword))
            column_filters.extend((
                column("measure_id", table="variable_browser").like(keyword),
                column("measure_name", table="variable_browser").like(keyword),
                column("description", table="variable_browser").like(keyword),
            ))
            query = query.where(reduce(
                lambda left, right: left.or_(right),  # type: ignore
                column_filters,
            ))

        if instrument_name:
            query = query.where(
                f"variable_browser.instrument_name = {instrument_name}",
            )
        if sort_by:
            column_to_sort: Any
            match sort_by:
                case "instrument":
                    column_to_sort = column(
                        "measure_id", self.variable_browser.alias_or_name)
                case "measure":
                    column_to_sort = column(
                        "measure_name", self.variable_browser.alias_or_name)
                case "measure_type":
                    column_to_sort = column(
                        "measure_type", self.variable_browser.alias_or_name)
                case "description":
                    column_to_sort = column(
                        "description", self.variable_browser.alias_or_name)
                case _:
                    regression = sort_by.split(".")
                    if len(regression) != 2:
                        raise ValueError(f"{sort_by} is an invalid sort column")
                    regression_id, sex = regression
  
                    reg_table = joined_tables[regression_id]
                    if sex == "male":
                        col_name = f"{regression_id}_pvalue_regression_male"
                    elif sex == "female":
                        col_name = f"{regression_id}_pvalue_regression_female"
  
                    column_to_sort = column(col_name)
            if order_by == "desc":
                query = query.order_by(f"{column_to_sort} DESC")
            else:
                query = query.order_by(f"{column_to_sort} ASC")
        else:
            query = query.order_by(
                "variable_browser.measure_id ASC",
            )

        return cast(expressions.Select, to_duckdb_transpile(query))

    def search_measures(
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by:  str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Find measures by keyword search."""
        query = self.build_measures_query(
            instrument_name,
            keyword,
            sort_by,
            order_by,
        )
        if page:
            query = query.limit(self.PAGE_SIZE).offset(
                self.PAGE_SIZE * (page - 1),
            )

        cursor = self.connection
        with cursor:
            rows = self.connection.execute(query).fetchall()
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

    def search_measures_df(
        self, instrument_name: str | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        """Find measures and return a dataframe with values."""
        query = self.build_measures_query(instrument_name, keyword)
        # execute query and .df()

        return self.connection.execute(query).df()

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

def safe_db_name(name: str) -> str:
    name = name.replace(".", "_").replace("-", "_").replace(" ", "_").lower()
    name = name.replace("/", "_")
    if name[0].isdigit():
        name = f"_{name}"
    return name


def generate_instrument_table_name(instrument_name: str) -> str:
    instrument_name = safe_db_name(instrument_name)
    return f"{instrument_name}_measure_values"
