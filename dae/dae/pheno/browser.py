from __future__ import annotations

import textwrap
from collections.abc import Iterator
from functools import reduce
from typing import Any

import duckdb
import sqlglot
from duckdb import ConstraintException
from sqlglot import column, expressions, select
from sqlglot.expressions import (
    Count,
    Null,
    alias_,
    delete,
    insert,
    table_,
    update,
    values,
)

from dae.pheno.common import MeasureType
from dae.utils.sql_utils import to_duckdb_transpile


class PhenoBrowser:
    """Class for handling saving and loading of phenotype browser data."""

    PAGE_SIZE = 1001

    def __init__(
        self, dbfile: str, *, read_only: bool = True,
    ):
        self.dbfile = dbfile
        self.connection = duckdb.connect(
            f"{dbfile}", read_only=read_only)
        if not read_only:
            PhenoBrowser.create_browser_tables(self.connection)
        self.variable_browser = table_("variable_browser")
        self.regressions = table_("regression")
        self.regression_values = table_("regression_values")
        self.is_legacy = self._is_browser_legacy()

    def _is_browser_legacy(self) -> bool:
        """Check if the database is legacy."""
        with self.connection.cursor() as cursor:
            columns = cursor.execute(
                "DESCRIBE " + self.variable_browser.alias_or_name,
            ).fetchall()
            column_names = [col[0] for col in columns]
            if "instrument_description" not in column_names:
                return True
        return False

    @staticmethod
    def create_browser_tables(conn: duckdb.DuckDBPyConnection) -> None:
        """Create tables for the browser DB."""
        create_variable_browser = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE IF NOT EXISTS variable_browser(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR NOT NULL,
                instrument_description VARCHAR,
                measure_name VARCHAR NOT NULL,
                measure_type INT NOT NULL,
                description VARCHAR,
                values_domain VARCHAR,
                figure_distribution_small VARCHAR,
                figure_distribution VARCHAR
            );
            CREATE UNIQUE INDEX IF NOT EXISTS variable_browser_measure_id_idx
                ON variable_browser (measure_id);
            CREATE INDEX IF NOT EXISTS variable_browser_instrument_name_idx
                ON variable_browser (instrument_name);
            CREATE INDEX IF NOT EXISTS variable_browser_measure_name_idx
                ON variable_browser (measure_name);
            """,
        ))

        create_regression = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE IF NOT EXISTS regression(
                regression_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR,
                measure_name VARCHAR NOT NULL,
                display_name VARCHAR,
            );
            CREATE UNIQUE INDEX IF NOT EXISTS regression_regression_id_idx
                ON regression (regression_id);
            """,
        ))

        create_regression_values = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE IF NOT EXISTS regression_values(
                regression_id VARCHAR NOT NULL,
                measure_id VARCHAR NOT NULL,
                figure_regression VARCHAR,
                figure_regression_small VARCHAR,
                pvalue_regression_male DOUBLE,
                pvalue_regression_female DOUBLE,
                PRIMARY KEY (regression_id, measure_id)
            );
            CREATE INDEX IF NOT EXISTS regression_values_regression_id_idx
                ON regression_values (regression_id);
            CREATE INDEX IF NOT EXISTS regression_values_measure_id_idx
                ON regression_values (measure_id);
            """,
        ))
        queries = [
            *create_variable_browser,
            *create_regression,
            *create_regression_values,
        ]
        with conn.cursor() as cursor:
            for query in queries:
                cursor.execute(to_duckdb_transpile(query))

    def save(self, v: dict[str, Any]) -> None:
        """Save measure values into the database."""
        query = to_duckdb_transpile(insert(
            values([(*v.values(),)]),
            self.variable_browser,
            columns=[*v.keys()],
        ))
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
        except ConstraintException:  # pylint: disable=broad-except
            measure_id = v["measure_id"]

            delete_query = to_duckdb_transpile(delete(
                self.variable_browser,
            ).where("measure_id").eq(measure_id))
            with self.connection.cursor() as cursor:
                cursor.execute(delete_query)
                cursor.execute(query)

    def save_regression(self, reg: dict[str, str]) -> None:
        """Save regressions into the database."""
        query = to_duckdb_transpile(insert(
            values([(*reg.values(),)]),
            self.regressions,
            columns=[*reg.keys()],
        ))
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
        except ConstraintException:  # pylint: disable=broad-except
            regression_id = reg["regression_id"]
            del reg["regression_id"]
            update_query = to_duckdb_transpile(update(
                self.regressions, reg,
            ).where("regression_id").eq(regression_id))
            with self.connection.cursor() as cursor:
                cursor.execute(update_query)

    def save_regression_values(self, reg: dict[str, str]) -> None:
        """Save regression values into the databases."""
        query = insert(
            values([(*reg.values(),)]),
            self.regression_values,
            columns=[*reg.keys()],
        )
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(to_duckdb_transpile(query))
        except ConstraintException:  # pylint: disable=broad-except
            regression_id = reg["regression_id"]
            measure_id = reg["measure_id"]

            del reg["regression_id"]
            del reg["measure_id"]
            update_query = to_duckdb_transpile(update(
                self.regression_values, reg,
                where=(
                    f"regression_id = '{regression_id}' AND "
                    f"measure_id = '{measure_id}'"
                ),
            ))
            with self.connection.cursor() as cursor:
                cursor.execute(update_query)

    def _build_ilike(
            self,
            keyword: str, col: expressions.Column) -> expressions.Escape:
        return expressions.Escape(this=col.ilike(keyword), expression="'/'")

    def _build_measures_query(
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> tuple[expressions.Select, list[expressions.Alias]]:
        """Find measures by keyword search."""

        joined_tables = {}
        regression_ids = self.regression_ids
        reg_cols = []

        if not self.is_legacy:
            instrument_description_column = column(
                "instrument_description", self.variable_browser.alias_or_name,
            )
        else:
            instrument_description_column = alias_(
                Null(),
                "instrument_description",
            )

        columns = [
            column("measure_id", self.variable_browser.alias_or_name),
            column("instrument_name", self.variable_browser.alias_or_name),
            instrument_description_column,
            column("measure_name", self.variable_browser.alias_or_name),
            column("measure_type", self.variable_browser.alias_or_name),
            column("description", self.variable_browser.alias_or_name),
            column("values_domain", self.variable_browser.alias_or_name),
            column("figure_distribution_small",
                self.variable_browser.alias_or_name),
            column("figure_distribution", self.variable_browser.alias_or_name),
        ]

        query = select(*columns).from_(self.variable_browser)

        for regression_id in regression_ids:
            reg_table = self.regression_values.as_(regression_id)
            measure_id_col = column(
                "measure_id", self.variable_browser.alias_or_name)
            reg_m_id = column("measure_id", reg_table.alias)
            reg_id_col = column("regression_id", reg_table.alias)
            query = query.join(
                reg_table,
                on=sqlglot.condition(
                    measure_id_col.eq(reg_m_id)
                    .and_(reg_id_col.eq(regression_id)),
                ),
                join_type="LEFT OUTER",
            )
            joined_tables[regression_id] = reg_table
            cols = [
                column(
                    "figure_regression", table=reg_table.alias_or_name,
                ).as_(f"{regression_id}_figure_regression"),
                column(
                    "figure_regression_small", table=reg_table.alias_or_name,
                ).as_(f"{regression_id}_figure_regression_small"),
                column(
                    "pvalue_regression_male", table=reg_table.alias_or_name,
                ).as_(f"{regression_id}_pvalue_regression_male"),
                column(
                    "pvalue_regression_female", table=reg_table.alias_or_name,
                ).as_(f"{regression_id}_pvalue_regression_female"),
            ]

            reg_cols.extend(cols)
            query = query.select(*cols)

        query = query.distinct()

        if keyword:
            query = self._measures_query_by_keyword(
                query, keyword, instrument_name,
            )

        if instrument_name:
            query = query.where(
                f"variable_browser.instrument_name = '{instrument_name}'",
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
                        raise ValueError(
                            f"{sort_by} is an invalid sort column",
                        )
                    regression_id, sex = regression

                    if sex not in ("male", "female"):
                        raise ValueError(
                            f"{sort_by} is an invalid sort column",
                        )
                    column_to_sort = column(
                        f"{regression_id}_pvalue_regression_{sex}",
                    )
            if order_by == "desc":
                query = query.order_by(f"{column_to_sort} DESC")
            else:
                query = query.order_by(f"{column_to_sort} ASC")
        else:
            query = query.order_by(
                "variable_browser.measure_id ASC",
            )

        return query, reg_cols

    def _build_measures_count_query(
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
    ) -> expressions.Select:
        """Count measures by keyword search."""

        count = Count(this="*")

        query = select(count).from_(self.variable_browser)

        query = query.distinct()

        if keyword:
            query = self._measures_query_by_keyword(
                query, keyword, instrument_name,
            )

        if instrument_name:
            query = query.where(
                f"variable_browser.instrument_name = '{instrument_name}'",
            )

        return query

    def _measures_query_by_keyword(
        self,
        query: expressions.Select,
        keyword: str,
        instrument_name: str | None = None,
    ) -> expressions.Select:
        column_filters = []
        keyword = keyword.replace("/", "//")\
            .replace("%", r"/%").replace("_", r"/_")
        keyword = f"%{keyword}%"
        if not instrument_name:
            column_filters.append(
                self._build_ilike(
                    keyword,
                    column("instrument_name", table="variable_browser"),
                ),
            )
        column_filters.extend((
            self._build_ilike(
                keyword,
                column("measure_id", table="variable_browser"),
            ),
            self._build_ilike(
                keyword,
                column("measure_name", table="variable_browser"),
            ),
            self._build_ilike(
                keyword,
                column("description", table="variable_browser"),
            ),
        ))

        return query.where(reduce(
            lambda left, right: left.or_(right),  # type: ignore
            column_filters,
        ))

    def search_measures(
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by:  str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Find measures by keyword search."""
        query, reg_cols = self._build_measures_query(
            instrument_name,
            keyword,
            sort_by,
            order_by,
        )
        reg_col_names = [reg_col.alias for reg_col in reg_cols]

        if page is None:
            page = 1

        query = query.limit(self.PAGE_SIZE).offset(
            self.PAGE_SIZE * (page - 1),
        )

        query_str = to_duckdb_transpile(query)

        with self.connection.cursor() as cursor:
            rows = cursor.execute(query_str).fetchall()
            for row in rows:
                yield {
                    "measure_id": row[0],
                    "instrument_name": row[1],
                    "instrument_description": row[2],
                    "measure_name": row[3],
                    "measure_type": MeasureType(row[4]),
                    "description": row[5],
                    "values_domain": row[6],
                    "figure_distribution_small": row[7],
                    "figure_distribution": row[8],
                    **dict(zip(reg_col_names, row[9:], strict=True)),
                }

    def count_measures(
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
        page: int | None = None,
    ) -> int:
        """Find measures by keyword search."""
        query = self._build_measures_count_query(
            instrument_name,
            keyword,
        )

        if page is None:
            page = 1

        query = query.limit(self.PAGE_SIZE).offset(
            self.PAGE_SIZE * (page - 1),
        )

        query_str = to_duckdb_transpile(query)

        with self.connection.cursor() as cursor:
            rows = cursor.execute(query_str).fetchall()
            return int(rows[0][0]) if rows else 0

    @property
    def regression_ids(self) -> list[str]:
        query = to_duckdb_transpile(select(
            column("regression_id", self.regressions.alias_or_name),
        ).from_(self.regressions))
        with self.connection.cursor() as cursor:
            return [
                x[0] for x in cursor.execute(query).fetchall()
            ]

    @property
    def regression_display_names(self) -> dict[str, str]:
        """Return regressions display name."""
        res = {}
        query = to_duckdb_transpile(select(
            column("regression_id", self.regressions.alias_or_name),
            column("display_name", self.regressions.alias_or_name),
        ).from_(self.regressions))
        with self.connection.cursor() as cursor:
            for row in cursor.execute(query).fetchall():
                res[row[0]] = row[1]
        return res

    @property
    def regression_display_names_with_ids(self) -> dict[str, Any]:
        """Return regression display names with measure IDs."""
        res = {}
        query = to_duckdb_transpile(select(
            column("regression_id", self.regressions.alias_or_name),
            column("display_name", self.regressions.alias_or_name),
            column("instrument_name", self.regressions.alias_or_name),
            column("measure_name", self.regressions.alias_or_name),
        ).from_(self.regressions))
        with self.connection.cursor() as cursor:
            for row in cursor.execute(query).fetchall():
                res[row[0]] = {
                    "display_name": row[1],
                    "instrument_name": row[2],
                    "measure_name": row[3],
                }
        return res

    @property
    def has_descriptions(self) -> bool:
        """Check if the database has a description data."""
        query = to_duckdb_transpile(select("COUNT(*)").from_(
            self.variable_browser,
        ).where("description IS NOT NULL"))
        with self.connection.cursor() as cursor:
            row = cursor.execute(query).fetchone()
            if row is None:
                return False
            return bool(row[0])
