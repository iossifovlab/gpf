from __future__ import annotations

from collections.abc import Generator
from functools import reduce
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd
from sqlglot import column, expressions, select, table

from dae.pheno.common import MeasureType
from dae.utils.sql_utils import glot_and, to_duckdb_transpile
from dae.variants.attributes import Role, Sex, Status


class PhenoDb:  # pylint: disable=too-many-instance-attributes
    """Class that manages access to phenotype databases."""

    def __init__(
            self, dbfile: str, *, read_only: bool = True,
    ) -> None:
        self.dbfile = dbfile
        self.connection = duckdb.connect(
            f"{dbfile}", read_only=read_only)
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
            query = query.where(columns[4]).eq(measure_type.value)

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

    def _get_measure_values_query(
        self,
        measure_ids: list[str],
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        roles: list[Role] | None = None,
    ) -> tuple[str, list[expressions.Column]]:
        assert isinstance(measure_ids, list)
        assert len(measure_ids) >= 1
        assert len(self.instrument_values_tables) > 0

        instrument_tables = {}

        for measure_id in measure_ids:
            instrument, _ = measure_id.split(".", maxsplit=1)
            instrument_table = table(generate_instrument_table_name(instrument))
            instrument_tables[instrument] = instrument_table

        union_queries = [
            select(
                column("person_id", table.alias_or_name),
                column("family_id", table.alias_or_name),
                column("role", table.alias_or_name),
                column("status", table.alias_or_name),
                column("sex", table.alias_or_name),
            ).from_(table)
            for table in instrument_tables.values()
        ]
        instrument_people = reduce(
            lambda left, right: left.union(right),  # type: ignore
            union_queries,
        ).subquery(alias="instrument_people")

        person_id_col = column("person_id", instrument_people.alias_or_name)

        output_cols = [
            person_id_col,
            column("family_id", instrument_people.alias_or_name),
            column("role", instrument_people.alias_or_name),
            column("status", instrument_people.alias_or_name),
            column("sex", instrument_people.alias_or_name),
        ]

        query = select(*output_cols).from_(instrument_people)
        joined = set()
        for measure_id in measure_ids:
            instrument, measure = measure_id.split(".", maxsplit=1)
            instrument_table = instrument_tables[instrument]
            if instrument not in joined:
                left_col = person_id_col.sql()
                right_col = column(
                    "person_id", instrument_table.alias_or_name,
                ).sql()
                measure_col = column(
                    safe_db_name(measure),
                    instrument_table.alias_or_name,
                ).as_(measure_id)
                query = query.select(
                    measure_col,
                ).join(
                    instrument_table,
                    on=f"{left_col} = {right_col}",
                    join_type="FULL OUTER",
                )
                joined.add(instrument)
                output_cols.append(cast(expressions.Column, measure_col))
            else:
                assert query is not None
                measure_col = column(
                    safe_db_name(measure),
                    instrument_table.alias_or_name,
                ).as_(measure_id)
                query = query.select(
                    measure_col,
                )
                output_cols.append(cast(expressions.Column, measure_col))

        assert query is not None

        empty_result = False
        cols_in = []
        if person_ids is not None:
            if len(person_ids) == 0:
                empty_result = True
            else:
                col = person_id_col
                cols_in.append(col.isin(*person_ids))
        if family_ids is not None:
            if len(family_ids) == 0:
                empty_result = True
            else:
                col = column(
                    "family_id",
                    instrument_people.alias_or_name,
                )
                cols_in.append(col.isin(*family_ids))
        if roles is not None:
            if len(roles) == 0:
                empty_result = True
            else:
                col = column(
                    "role",
                    instrument_people.alias_or_name,
                )
                cols_in.append(col.isin(*[r.value for r in roles]))

        query = query.order_by(person_id_col)

        if cols_in:
            query = query.where(reduce(glot_and, cols_in))

        if empty_result:
            query = query.where("1=2")

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
    """Convert a string to a db-friendly string."""
    if name == "":
        raise ValueError("The name cannot be empty")
    name = name.replace(".", "_").replace("-", "_").replace(" ", "_").lower()
    name = name.replace("/", "_")
    if name[0].isdigit():
        name = f"_{name}"
    return name


def generate_instrument_table_name(instrument_name: str) -> str:
    instrument_name = safe_db_name(instrument_name)
    return f"{instrument_name}_measure_values"
