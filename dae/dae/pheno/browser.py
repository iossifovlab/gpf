from __future__ import annotations

import textwrap
from collections.abc import Iterator
from functools import reduce
from typing import Any

import duckdb
import sqlglot
from duckdb import (
    ConstraintException,
)
from sqlglot import column, expressions, select
from sqlglot.expressions import (
    Count,
    Null,
    Table,
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
        self.instrument_descriptions = table_("instrument_descriptions")
        self.measure_descriptions = table_("measure_descriptions")
        self.is_legacy = self._is_browser_legacy()
        self._closed = False

    def _is_browser_legacy(self) -> bool:
        """Handle legacy databases."""
        with self.connection.cursor() as cursor:
            result = cursor.execute("SHOW TABLES").fetchall()
        tables = [row[0] for row in result]
        return bool(
            "instrument_descriptions" not in tables
            or "measure_descriptions" not in tables)

    def close(self) -> None:
        """Close the connection to the database."""
        if self.connection is not None and not self._closed:
            self.connection.close()
            self._closed = True

    @staticmethod
    def create_browser_tables(conn: duckdb.DuckDBPyConnection) -> None:
        """Create tables for the browser DB."""
        create_variable_browser = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE IF NOT EXISTS variable_browser(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                instrument_name VARCHAR NOT NULL,
                measure_name VARCHAR NOT NULL,
                measure_type INT NOT NULL,
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

        create_instrument_descriptions = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE IF NOT EXISTS instrument_descriptions(
                instrument_name VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                description VARCHAR,
            );
            CREATE UNIQUE INDEX IF NOT EXISTS
                instrument_descriptions_instrument_name_idx
                ON instrument_descriptions (instrument_name);
            """,
        ))

        create_measure_descriptions = sqlglot.parse(textwrap.dedent(
            """
            CREATE TABLE IF NOT EXISTS measure_descriptions(
                measure_id VARCHAR NOT NULL UNIQUE PRIMARY KEY,
                description VARCHAR,
            );
            CREATE UNIQUE INDEX IF NOT EXISTS
                measure_descriptions_measure_id_idx
                ON measure_descriptions (measure_id);
            """,
        ))
        queries = [
            *create_variable_browser,
            *create_regression,
            *create_regression_values,
            *create_instrument_descriptions,
            *create_measure_descriptions,
        ]
        with conn.cursor() as cursor:
            for query in queries:
                cursor.execute(to_duckdb_transpile(query))

    def save(self, v: dict[str, Any]) -> None:
        """Save measure values into the database."""
        with self.connection.cursor() as cursor:
            if not self.is_legacy:
                instrument_desc_query = to_duckdb_transpile(insert(
                    values([(
                        v["instrument_name"],
                        v.get("instrument_description", ""),
                    )]),
                    self.instrument_descriptions,
                    columns=["instrument_name", "description"],
                ))
                v.pop("instrument_description", None)

                try:
                    cursor.execute(instrument_desc_query)
                except ConstraintException:
                    delete_instrument_desc_query = to_duckdb_transpile(delete(
                        self.instrument_descriptions,
                    ).where("instrument_name").eq(v["instrument_name"]))
                    cursor.execute(delete_instrument_desc_query)
                    cursor.execute(instrument_desc_query)

                measure_desc_query = to_duckdb_transpile(insert(
                    values([(
                        v["measure_id"],
                        v.get("description", ""),
                    )]),
                    self.measure_descriptions,
                    columns=["measure_id", "description"],
                ))
                v.pop("description", None)

                try:
                    cursor.execute(measure_desc_query)
                except ConstraintException:
                    delete_measure_desc_query = to_duckdb_transpile(delete(
                        self.measure_descriptions,
                    ).where("measure_id").eq(v["measure_id"]))
                    cursor.execute(delete_measure_desc_query)
                    cursor.execute(measure_desc_query)

            measure_query = to_duckdb_transpile(insert(
                values([(*v.values(),)]),
                self.variable_browser,
                columns=[*v.keys()],
            ))

            try:
                cursor.execute(measure_query)
            except ConstraintException:
                delete_measure_query = to_duckdb_transpile(delete(
                    self.variable_browser,
                ).where("measure_id").eq(v["measure_id"]))
                cursor.execute(delete_measure_query)
                cursor.execute(measure_query)

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

    def save_regression_values(self, reg: dict[str, Any]) -> None:
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

        columns = [
            column("measure_id", self.variable_browser.alias_or_name),
            column("instrument_name", self.variable_browser.alias_or_name),
            column("measure_name", self.variable_browser.alias_or_name),
            column("measure_type", self.variable_browser.alias_or_name),
            column("values_domain", self.variable_browser.alias_or_name),
            column(
                "figure_distribution_small",
                self.variable_browser.alias_or_name),
            column("figure_distribution", self.variable_browser.alias_or_name),
        ]

        query = select(*columns).from_(self.variable_browser)

        variable_browser_instrument_name_col = column(
            "instrument_name", self.variable_browser.alias_or_name)
        variable_browser_measure_id_col = column(
                "measure_id", self.variable_browser.alias_or_name)

        if not self.is_legacy:
            instrument_descriptions_instrument_name_col = column(
                "instrument_name", self.instrument_descriptions.alias_or_name)
            instrument_descriptions_description_col = column(
                "description", self.instrument_descriptions.alias_or_name)

            query = query.join(
                    self.instrument_descriptions,
                    on=sqlglot.condition(
                        variable_browser_instrument_name_col.eq(
                            instrument_descriptions_instrument_name_col,
                        ),
                    ),
                    join_type="LEFT OUTER",
                )
            query = query.select(
                instrument_descriptions_description_col.as_(
                    "instrument_description",
                ))

            measure_descriptions_measure_id_col = column(
                "measure_id", self.measure_descriptions.alias_or_name)
            measure_descriptions_description_col = column(
                "description", self.measure_descriptions.alias_or_name)

            query = query.join(
                    self.measure_descriptions,
                    on=sqlglot.condition(
                        variable_browser_measure_id_col.eq(
                            measure_descriptions_measure_id_col,
                        ),
                    ),
                    join_type="LEFT OUTER",
                )
            query = query.select(measure_descriptions_description_col)
        else:
            query = query.select(alias_(Null(), "instrument_description"))
            query = query.select(alias_(Null(), "description"))

        for regression_id in regression_ids:
            reg_table = self.regression_values.as_(regression_id)
            reg_m_id = column("measure_id", reg_table.alias)
            reg_id_col = column("regression_id", reg_table.alias)
            query = query.join(
                reg_table,
                on=sqlglot.condition(
                    variable_browser_measure_id_col.eq(reg_m_id)
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
                    "measure_name": row[2],
                    "measure_type": MeasureType(row[3]),
                    "values_domain": row[4],
                    "figure_distribution_small": row[5],
                    "figure_distribution": row[6],
                    "instrument_description": row[7],
                    "description": row[8],
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

    def save_descriptions(
        self,
        table: Table,
        descriptions: dict[str, str],
    ) -> None:
        """Save instrument or measure descriptions."""
        descriptions_table = table.alias_or_name
        with self.connection.cursor() as cursor:
            delete_rows = delete(table.alias_or_name)
            query = insert(
                values([tuple(i) for i in descriptions.items()]),
                descriptions_table,
            )
            cursor.execute(to_duckdb_transpile(delete_rows))
            cursor.execute(to_duckdb_transpile(query))

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
    def has_instrument_descriptions(self) -> bool:
        """Check if the database has instrument description data."""
        if self.is_legacy:
            return False
        query = to_duckdb_transpile(select("COUNT(*)").from_(
            self.instrument_descriptions,
        ).where("description IS NOT NULL"))
        with self.connection.cursor() as cursor:
            row = cursor.execute(query).fetchone()
            if row is None:
                return False
            return bool(row[0])

    @property
    def has_measure_descriptions(self) -> bool:
        """Check if the database has measure description data."""
        if self.is_legacy:
            return False
        query = to_duckdb_transpile(select("COUNT(*)").from_(
            self.measure_descriptions,
        ).where("description IS NOT NULL"))
        with self.connection.cursor() as cursor:
            row = cursor.execute(query).fetchone()
            if row is None:
                return False
            return bool(row[0])
