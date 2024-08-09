from __future__ import annotations

from collections.abc import Generator, Iterator
from functools import reduce
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import sqlglot
from duckdb import ConstraintException
from sqlglot import column, expressions, select, table
from sqlglot.expressions import delete, insert, update, values

from dae.pheno.common import MeasureType
from dae.utils.sql_utils import glot_and, to_duckdb_transpile
from dae.variants.attributes import Role, Sex, Status


class PhenoDb:  # pylint: disable=too-many-instance-attributes
    """Class that manages access to phenotype databases."""

    PAGE_SIZE = 1001

    def __init__(
            self, dbfile: str, *, read_only: bool = True,
    ) -> None:
        self.dbfile = dbfile
        self.connection = duckdb.connect(
            f"{dbfile}", read_only=read_only)
        self.variable_browser = table("variable_browser")
        self.regressions = table("regression")
        self.regression_values = table("regression_values")
        self.family = table("family")
        self.person = table("person")
        self.measure = table("measure")
        self.instrument = table("instrument")
        self.instrument_values_tables = self.find_instrument_values_tables()

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

    def find_instrument_values_tables(self) -> dict[str, expressions.Table]:
        """
        Create instrument values tables.

        Each row is basically a list of every measure value in the instrument
        for a certain person.
        """
        query = to_duckdb_transpile(select(
            "instrument_name",
            "table_name",
        ).from_(self.instrument))

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

    def save(self, v: dict[str, str | None]) -> None:
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
            ).where(f"measure_id = {measure_id}"))
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
            update_query = update(
                self.regressions, reg,
                where=f"regression_id = {regression_id}",
            )
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
                cursor.execute(query)
        except ConstraintException:  # pylint: disable=broad-except
            regression_id = reg["regression_id"]
            measure_id = reg["measure_id"]

            del reg["regression_id"]
            del reg["measure_id"]
            update_query = update(
                self.regression_values, reg,
                where=(
                    f"regression_id = {regression_id} AND "
                    f"measure_id = {measure_id}"
                ),
            )
            with self.connection.cursor() as cursor:
                cursor.execute(update_query)

    def get_browser_measure(self, measure_id: str) -> dict | None:
        """Get measure description from phenotype browser database."""
        query = to_duckdb_transpile(select(
            column("*", self.variable_browser.alias_or_name),
        ).from_(self.variable_browser).where(f"measure_id = {measure_id}"))
        with self.connection.cursor() as cursor:
            rows = cursor.execute(query).df()
            if rows:
                return rows.to_dict("records")[0]
            return None

    def build_measures_query(
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

        query = select(
            f"{self.variable_browser.alias_or_name}.*",
        ).from_(self.variable_browser)

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

                    reg_table = joined_tables[regression_id]
                    if sex == "male":
                        col_name = f"{regression_id}_pvalue_regression_male"
                    else:
                        if sex != "female":
                            raise ValueError(
                                f"{sort_by} is an invalid sort column",
                            )
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

        return query, reg_cols

    def get_measures_df(
        self,
        instrument: str | None = None,
        measure_type: MeasureType | None = None,
    ) -> pd.DataFrame:
        """
        Return data frame containing measures information.

        `instrument` -- an instrument name which measures should be
        returned. If not specified all type of measures are returned.

        `measure_type` -- a type ('continuous', 'ordinal' or 'categorical')
        of measures that should be returned. If not specified all
        type of measures are returned.

        Each row in the returned data frame represents given measure.

        Columns in the returned data frame are: `measure_id`, `measure_name`,
        `instrument_name`, `description`, `stats`, `min_value`, `max_value`,
        `value_domain`, `has_probands`, `has_siblings`, `has_parents`,
        `default_filter`.
        """

        measure_table = self.measure
        columns = [
            column("measure_id", measure_table.alias_or_name),
            column("instrument_name", measure_table.alias_or_name),
            column("measure_name", measure_table.alias_or_name),
            column("description", measure_table.alias_or_name),
            column("measure_type", measure_table.alias_or_name),
            column("individuals", measure_table.alias_or_name),
            column("default_filter", measure_table.alias_or_name),
            column("values_domain", measure_table.alias_or_name),
            column("min_value", measure_table.alias_or_name),
            column("max_value", measure_table.alias_or_name),
        ]
        query: Any = select(*columns).from_(
            measure_table,
        ).where(f"{columns[4].sql()} IS NOT NULL")
        if instrument is not None:
            query = query.where(columns[1]).eq(instrument)
        if measure_type is not None:
            query = query.where(columns[4]).eq(measure_type)

        with self.connection.cursor() as cursor:
            df = cursor.execute(to_duckdb_transpile(query)).df()

        df_columns = [
            "measure_id",
            "measure_name",
            "instrument_name",
            "description",
            "individuals",
            "measure_type",
            "default_filter",
            "values_domain",
            "min_value",
            "max_value",
        ]
        return df[df_columns]

    def search_measures(
        self,
        instrument_name: str | None = None,
        keyword: str | None = None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by:  str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Find measures by keyword search."""
        query, reg_cols = self.build_measures_query(
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
                    "description": row[4],
                    "values_domain": row[5],
                    "figure_distribution_small": row[6],
                    "figure_distribution": row[7],
                    **dict(zip(reg_col_names, row[8:], strict=True)),
                }

    def search_measures_df(
        self, instrument_name: str | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        """Find measures and return a dataframe with values."""
        query = to_duckdb_transpile(
            self.build_measures_query(instrument_name, keyword))
        # execute query and .df()

        return self.connection.execute(query).df()

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

    def _get_measure_values_query(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> tuple[str, list[expressions.Expression]]:
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert len(self.instrument_values_tables) > 0

        query = None
        instrument_tables = {}
        output_cols = []
        for measure_id in measure_ids:
            instrument, measure = measure_id.split(".")
            instrument_table = table(generate_instrument_table_name(instrument))
            if instrument not in instrument_tables:
                if query is None:
                    first_instrument_table = instrument_table
                    cols = [
                        column("person_id", instrument_table.alias_or_name),
                        column("family_id", instrument_table.alias_or_name),
                        column("role", instrument_table.alias_or_name),
                        column("status", instrument_table.alias_or_name),
                        column("sex", instrument_table.alias_or_name),
                        column(
                            safe_db_name(measure),
                            instrument_table.alias_or_name,
                        ).as_(measure_id),
                    ]
                    query = select(
                        *cols,
                    ).from_(instrument_table)
                    output_cols.extend(cols)
                else:
                    left_col = column(
                        "person_id", first_instrument_table.alias_or_name,
                    ).sql()
                    right_col = column(
                        "person_id", instrument_table.alias_or_name,
                    ).sql()
                    measure_col = column(
                        safe_db_name(measure),
                        instrument_table.alias_or_name,
                    ).as_(measure_id)
                    query = query.select(
                        measure_col,
                    ).join(instrument_table, on=f"{left_col} = {right_col}")
                    output_cols.append(measure_col)

                instrument_tables[instrument] = instrument_table
            else:
                assert query is not None
                measure_col = column(
                    safe_db_name(measure),
                    instrument_table.alias_or_name,
                ).as_(measure_id)
                query = query.select(
                    measure_col,
                )
                output_cols.append(measure_col)

        assert query is not None

        cols_in = []
        if person_ids is not None:
            col = column(
                "person_id",
                first_instrument_table.alias_or_name,
            )
            cols_in.append(col.isin(*person_ids))
        if family_ids is not None:
            col = column(
                "family_id",
                first_instrument_table.alias_or_name,
            )
            cols_in.append(col.isin(*family_ids))
        if roles is not None:
            col = column(
                "role",
                first_instrument_table.alias_or_name,
            )
            cols_in.append(col.isin(*[r.value for r in roles]))

        query = query.order_by(column(
            "person_id",
            first_instrument_table.alias_or_name,
        ))

        if cols_in:
            query = query.where(reduce(glot_and, cols_in))

        return (
            to_duckdb_transpile(query),
            output_cols,
        )

    def get_people_measure_values(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Yield lines from measure values tables."""
        query, output_cols = self._get_measure_values_query(
            measure_ids, person_ids, family_ids, roles,
        )
        with self.connection.cursor() as cursor:
            result = cursor.execute(query)

            for row in result.fetchall():
                output = {
                    col.alias_or_name: row[idx]
                    for idx, col in enumerate(output_cols)
                }
                output["role"] = Role.to_name(output["role"])
                output["status"] = Status.to_name(output["status"])
                output["sex"] = Sex.to_name(output["sex"])
                yield output

    def get_people_measure_values_df(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> pd.DataFrame:
        """Return dataframe from measure values tables."""
        query, _ = self._get_measure_values_query(
            measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles,
        )

        with self.connection.cursor() as cursor:
            result = cursor.execute(query)

            df = result.df()
            df["sex"] = df["sex"].transform(Sex.from_value)
            df["status"] = df["status"].transform(Status.from_value)
            df["role"] = df["role"].transform(Role.from_value)
            return df


def safe_db_name(name: str) -> str:
    name = name.replace(".", "_").replace("-", "_").replace(" ", "_").lower()
    name = name.replace("/", "_")
    if name[0].isdigit():
        name = f"_{name}"
    return name


def generate_instrument_table_name(instrument_name: str) -> str:
    instrument_name = safe_db_name(instrument_name)
    return f"{instrument_name}_measure_values"
