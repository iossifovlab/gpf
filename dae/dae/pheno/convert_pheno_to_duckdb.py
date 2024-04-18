from collections.abc import Iterator, Mapping
from typing import Any, Dict, Optional, Union, cast

import duckdb
import pandas as pd
from box import Box
from sqlalchemy import (
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    desc,
    func,
    or_,
)
from sqlalchemy.sql import Select, select, text
from sqlalchemy.sql.schema import PrimaryKeyConstraint, UniqueConstraint

from dae.pheno.common import MeasureType
from dae.variants.attributes import Role, Sex, Status


class LegacyPhenoDb:  # pylint: disable=too-many-instance-attributes
    """
    Class that manages access to phenotype databases.

    A copy of the old PhenoDb to support the migration tool.
    """

    STREAMING_CHUNK_SIZE = 25

    def __init__(
        self, dbfile: str, browser_dbfile: Optional[str] = None,
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
        self.measures: Table
        self.instruments: Table
        self.instrument_values_tables: dict[str, Table] = {}
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
        self.build_instruments_and_measures_table()
        self.build_instrument_values_tables()

        self.pheno_metadata.create_all(self.pheno_engine)

        self.build_browser()

    def build_instruments_and_measures_table(self) -> None:
        """Create tables for instruments and measures."""
        if getattr(self, "instruments", None) is None:
            self.instruments = Table(
                "instruments",
                self.pheno_metadata,
                Column("id", Integer(), primary_key=True),
                Column(
                    "instrument_name", String(64), nullable=False, index=True,
                ),
                Column("table_name", String(64), nullable=False),
            )

        if getattr(self, "measures", None) is None:
            self.measures = Table(
                "measures",
                self.pheno_metadata,
                Column("id", Integer(), primary_key=True),
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
                Column("instrument_id", ForeignKey("instruments.id")),
                Column("description", String(255)),
                Column("measure_type", Enum(MeasureType), index=True),
                Column("individuals", Integer()),
                Column("default_filter", String(255)),
                Column("min_value", Float(), nullable=True),
                Column("max_value", Float(), nullable=True),
                Column("values_domain", String(255), nullable=True),
                Column("rank", Integer(), nullable=True),
            )

        self.pheno_metadata.create_all(self.pheno_engine)

    def build_instrument_values_tables(self) -> None:
        """
        Create instrument values tables.

        Each row is basically a list of every measure value in the instrument
        for a certain person.
        """
        query = select(
            self.instruments.c.instrument_name,
            self.instruments.c.table_name,
        )
        with self.pheno_engine.connect() as connection:
            instruments_rows = connection.execute(query)
            instrument_table_names = {}
            instrument_measures: dict[str, list[str]] = {}
            for row in instruments_rows:
                instrument_table_names[row.instrument_name] = row.table_name
                instrument_measures[row.instrument_name] = []

        query = select(
            self.measures.c.measure_id,
            self.measures.c.measure_type,
            self.measures.c.db_column_name,
            self.instruments.c.instrument_name,
        ).join(self.instruments)
        with self.pheno_engine.connect() as connection:
            results = connection.execute(query)
            measure_columns = {}
            for result_row in results:
                instrument_measures[result_row.instrument_name].append(
                    result_row.measure_id,
                )
                if MeasureType.is_numeric(result_row.measure_type):
                    column_type: Union[Float, String] = Float()
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
                        Enum(Status),
                        nullable=False,
                        default=Status.unaffected,
                    ),
                    Column("sex", Enum(Sex), nullable=False),
                    *cols,
                    extend_existing=True,
                )

        self.pheno_metadata.create_all(self.pheno_engine)

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

    def _build_measures_subquery(
        self,
        measure_id_map: dict[str, str],
        measure_type_map: Mapping[str, Union[str, MeasureType]],
        measure_ids: list[str],
        measure_column_names: Optional[dict[str, str]] = None,
    ) -> Select:
        select_columns = [
            self.person.c.person_id,
            self.person.c.role,
            self.family.c.family_id,
            self.person.c.status,
            self.person.c.sex,
        ]
        query = select(
            self.measure.c.measure_id, self.measure.c.measure_type,
        )
        for m_id in measure_ids:
            measure_type = measure_type_map[m_id]
            if measure_type is None:
                raise ValueError(
                    f"bad measure: {m_id}; unknown value type",
                )
            col_name = m_id
            if measure_column_names is not None:
                col_name = measure_column_names[m_id]
            select_columns.append(cast(Column[Any], text(
                f"\"{m_id}_value\".value AS '{col_name}'",
            )))
        query = select(*select_columns).select_from(
            self.person.join(self.family),
        )

        for m_id in measure_ids:
            db_id = measure_id_map[m_id]
            measure_type = measure_type_map[m_id]
            measure_table = self.get_value_table(measure_type)
            table_alias = f"{m_id}_value"
            query = query.join(
                text(f'{measure_table.name} as "{table_alias}"'),
                text(
                    f'"{table_alias}".person_id = person.id AND '
                    f'"{table_alias}".measure_id = {db_id}',
                ),
                isouter=True,
            )

        query = query.order_by(desc(self.person.c.person_id))
        return query

    def clear_instruments_table(self, drop: bool = False) -> None:
        """Clear the instruments table."""
        if getattr(self, "instruments", None) is None:
            return
        with self.pheno_engine.begin() as connection:
            connection.execute(self.instruments.delete())
            if drop:
                self.instruments.drop(connection, checkfirst=False)
            connection.commit()

    def clear_measures_table(self, drop: bool = False) -> None:
        """Clear the measures table."""
        if getattr(self, "measures", None) is None:
            return
        with self.pheno_engine.begin() as connection:
            connection.execute(self.measures.delete())
            if drop:
                self.measures.drop(connection, checkfirst=False)
            connection.commit()

    def clear_instrument_values_tables(self, drop: bool = False) -> None:
        """Clear all instrument values tables."""
        if getattr(self, "instrument_values_tables", None) is None:
            return
        with self.pheno_engine.begin() as connection:
            for instrument_table in self.instrument_values_tables.values():
                connection.execute(instrument_table.delete())
                if drop:
                    instrument_table.drop(connection, checkfirst=False)
            connection.commit()

    def get_instrument_column_names(self) -> dict[str, list[str]]:
        """Return a map of instruments and their measure column names."""
        query = select(
            self.measures.c.db_column_name,
            self.instruments.c.instrument_name,
        ).join(self.instruments)
        with self.pheno_engine.connect() as connection:
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
        self, measure_ids: Optional[list[str]] = None,
    ) -> dict[str, str]:
        """Return measure column names mapped to their measure IDs."""
        query = select(
            self.measures.c.measure_id,
            self.measures.c.db_column_name,
        )
        if measure_ids is not None:
            query = query.where(self.measures.c.measure_id.in_(measure_ids))
        with self.pheno_engine.connect() as connection:
            results = connection.execute(query)

            measure_column_names = {}
            for result_row in results:
                measure_column_names[result_row.measure_id] = \
                    result_row.db_column_name
        return measure_column_names

    def get_measure_column_names_reverse(
        self, measure_ids: Optional[list[str]] = None,
    ) -> dict[str, str]:
        """Return measure column names mapped to their measure IDs."""
        query = select(
            self.measures.c.measure_id,
            self.measures.c.db_column_name,
        )
        if measure_ids is not None:
            query = query.where(self.measures.c.measure_id.in_(measure_ids))
        with self.pheno_engine.connect() as connection:
            results = connection.execute(query)

            measure_column_names = {}
            for result_row in results:
                measure_column_names[result_row.db_column_name] = \
                    result_row.measure_id
        return measure_column_names

    #  pylint: disable=too-many-branches
    def populate_instrument_values_tables(self, use_old: bool = False) -> None:
        """
        Populate the instrument values tables with values.

        Dependant on measures and instruments tables being populated and
        the original value tables being populated.
        """
        if getattr(self, "instrument_values_tables", None) is None:
            raise ValueError("No instrument values tables prepared")

        measure_id_map = {}
        measure_type_map = {}
        instrument_measures = {}
        measure_column_names = {}

        with self.pheno_engine.connect() as connection:
            if use_old:
                # Very important to use legacy 'measure' table here instead
                # Measure IDs will be mismatched when
                # collecting values otherwise
                query = select(
                    self.measure.c.id,
                    self.measure.c.measure_id,
                    self.measure.c.measure_type,
                )
            else:
                query = select(
                    self.measures.c.id,
                    self.measures.c.measure_id,
                    self.measures.c.measure_type,
                )
            results = connection.execute(query)
            for result_row in results:
                measure_id_map[result_row.measure_id] = result_row.id
                measure_type_map[result_row.measure_id] = \
                    result_row.measure_type

            query = select(
                self.measures.c.measure_id,
                self.measures.c.db_column_name,
                self.instruments.c.instrument_name,
            ).join(self.instruments)
            results = connection.execute(query)
            for result_row in results:
                if result_row.instrument_name not in instrument_measures:
                    instrument_measures[result_row.instrument_name] = [
                        result_row.measure_id,
                    ]
                else:
                    instrument_measures[result_row.instrument_name].append(
                        result_row.measure_id,
                    )
                measure_column_names[result_row.measure_id] = \
                    result_row.db_column_name

        measure_groups = self._split_measures_into_groups(
            cast(list[str], list(measure_id_map.keys())),
        )

        queries = []
        for group in measure_groups:
            queries.append(self._build_measures_subquery(
                cast(dict[str, str], measure_id_map),
                cast(dict[str, MeasureType], measure_type_map),
                group,
                measure_column_names,
            ))

        added_instruments = set()
        with self.pheno_engine.begin() as connection:
            query_results = zip(*[
                connection.execute(query) for query in queries
            ])
            for subquery_results in query_results:
                row = {}
                for fetched_row in subquery_results:
                    # pylint: disable=protected-access
                    row.update(fetched_row._mapping)

                instrument_values = {}
                for instrument_name, measures in instrument_measures.items():
                    skip = True
                    query_values = {
                        "person_id": row["person_id"],
                        "role": str(row["role"]),
                        "family_id": row["family_id"],
                        "status": row["status"],
                        "sex": row["sex"],
                    }
                    for measure in measures:
                        col_name = measure_column_names[measure]
                        value = row[col_name]
                        if value is not None:
                            skip = False
                        query_values[col_name] = value

                    if not skip:
                        instrument_values[instrument_name] = query_values

                for instrument_name, i_table in \
                        self.instrument_values_tables.items():
                    if instrument_name in instrument_values:
                        added_instruments.add(instrument_name)
                        values = instrument_values[instrument_name]
                        insert = i_table.insert().values(**values)
                        connection.execute(insert)

            connection.commit()

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
                "regression_id", "measure_id", name="regression_pkey",
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
                "instrument_name", "measure_name", name="measure_key",
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
                connection.commit()
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
                    & (self.regression_values.c.measure_id == measure_id),
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
        keyword: Optional[str] = None,
    ) -> Iterator[dict[str, Any]]:
        """Find measert by keyword search."""
        query_params = []

        if keyword:
            keyword = "%{}%".format(
                keyword.replace("%", r"\%").replace("_", r"\_"),
            )
            if not instrument_name:
                query_params.append(
                    self.variable_browser.c.instrument_name.like(
                        keyword, escape="\\",
                    ),
                )
            query_params.append(
                self.variable_browser.c.measure_id.like(keyword, escape="\\"),
            )
            query_params.append(
                self.variable_browser.c.measure_name.like(keyword, escape="\\"),
            )
            query_params.append(
                self.variable_browser.c.description.like(keyword, escape="\\"),
            )
            query = self.variable_browser.select().where(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name,
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
        keyword: Optional[str] = None,
    ) -> pd.DataFrame:
        """Find measures and return a dataframe with values."""
        query_params = []

        if keyword:
            keyword = "%{}%".format(
                keyword.replace("%", r"\%").replace("_", r"\_"),
            )
            if not instrument_name:
                query_params.append(
                    self.variable_browser.c.instrument_name.like(
                        keyword, escape="\\",
                    ),
                )
            query_params.append(
                self.variable_browser.c.measure_id.like(keyword, escape="\\"),
            )
            query_params.append(
                self.variable_browser.c.measure_name.like(keyword, escape="\\"),
            )
            query_params.append(
                self.variable_browser.c.description.like(keyword, escape="\\"),
            )
            query = self.variable_browser.select().where(or_(*query_params))
        else:
            query = self.variable_browser.select()

        if instrument_name:
            query = query.where(
                self.variable_browser.c.instrument_name == instrument_name,
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
                lambda x: x[0],
                connection.execute(selector)))

    @property
    def regression_display_names(self) -> Dict[str, str]:
        """Return regressions display name."""
        res = {}
        selector = select(
            self.regressions.c.regression_id, self.regressions.c.display_name,
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
                    .where(Column("description").isnot(None)),
                ).scalar(),
            )

    def get_value_table(
        self, value_type: Union[str, MeasureType],
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


def create_sqlite_phenodb(
    dbfile: str, browser_dbfile: Optional[str] = None,
) -> LegacyPhenoDb:
    db = LegacyPhenoDb(dbfile, browser_dbfile)
    db.build()
    return db


def build_instrument_values_tables(
    metadata: MetaData, sqlite_db: LegacyPhenoDb,
) -> dict[str, Table]:
    """Create and return instrument values tables."""
    instrument_values_tables: dict[str, Table] = {}
    query = select(
        sqlite_db.instruments.c.instrument_name,
        sqlite_db.instruments.c.table_name,
    )
    with sqlite_db.pheno_engine.connect() as connection:
        instruments_rows = connection.execute(query)
        instrument_table_names = {}
        instrument_measures: dict[str, list[str]] = {}
        for row in instruments_rows:
            instrument_table_names[row.instrument_name] = row.table_name
            instrument_measures[row.instrument_name] = []

    query = select(
        sqlite_db.measures.c.measure_id,
        sqlite_db.measures.c.measure_type,
        sqlite_db.measures.c.db_column_name,
        sqlite_db.instruments.c.instrument_name,
    ).join(sqlite_db.instruments)
    with sqlite_db.pheno_engine.connect() as connection:
        results = connection.execute(query)
        measure_columns: dict[str, Column] = {}
        for result_row in results:
            instrument_measures[result_row.instrument_name].append(
                result_row.measure_id,
            )
            if MeasureType.is_numeric(result_row.measure_type):
                column_type: Union[Float, String] = Float()
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

        if instrument_name not in instrument_values_tables:
            instrument_values_tables[instrument_name] = Table(
                table_name,
                metadata,
                Column(
                    "person_id",
                    String(16),
                    nullable=False,
                    unique=True,
                ),
                Column(
                    "family_id", String(64), nullable=False,
                ),
                Column("role", Integer(), nullable=False),
                Column(
                    "status",
                    Integer(),
                    nullable=False,
                    default=1,
                ),
                Column("sex", Integer(), nullable=False),
                *cols,
                extend_existing=True,
            )
    return instrument_values_tables


def create_duckdb_dbfile(
    dbfile: str, sqlite_db: LegacyPhenoDb,
) -> dict[str, Any]:
    """Create the base DuckDB dbfile used for migration."""
    duckdb_engine = create_engine(f"duckdb:///{dbfile}")
    metadata = MetaData()
    family_t = Table(
        "family",
        metadata,
        Column(
            "family_id",
            String(64),
            nullable=False,
            unique=True,
        ),
    )
    person_t = Table(
        "person",
        metadata,
        Column("family_id", String(64), nullable=False),
        Column("person_id", String(16), nullable=False),
        Column("role", Integer(), nullable=False),
        Column(
            "status",
            Integer(),
            nullable=False,
            default=1,
        ),
        Column("sex", Integer(), nullable=False),
        Column("sample_id", String(16), nullable=True),
        UniqueConstraint("family_id", "person_id", name="person_key"),
    )
    measure_t = Table(
        "measure",
        metadata,
        Column(
            "measure_id",
            String(128),
            nullable=False,
            unique=True,
        ),
        Column("db_column_name", String(128), nullable=False),
        Column("measure_name", String(64), nullable=False),
        Column("instrument_name", String(64), nullable=False),
        Column("description", String(255)),
        Column("measure_type", Integer()),
        Column("individuals", Integer()),
        Column("default_filter", String(255)),
        Column("min_value", Float(), nullable=True),
        Column("max_value", Float(), nullable=True),
        Column("values_domain", String(255), nullable=True),
        Column("rank", Integer(), nullable=True),
    )
    instrument_t = Table(
        "instrument",
        metadata,
        Column("instrument_name", String(64), nullable=False),
        Column("table_name", String(64), nullable=False),
    )

    instrument_values_tables = build_instrument_values_tables(
        metadata, sqlite_db,
    )

    variable_browser_t = Table(
        "variable_browser",
        metadata,
        Column(
            "measure_id",
            String(128),
            nullable=False,
            unique=True,
        ),
        Column("instrument_name", String(64), nullable=False),
        Column("measure_name", String(64), nullable=False),
        Column("measure_type", Integer(), nullable=False),
        Column("description", String(256)),
        Column("values_domain", String(256)),
        Column("figure_distribution_small", String(256)),
        Column("figure_distribution", String(256)),
    )

    regressions_t = Table(
        "regression",
        metadata,
        Column(
            "regression_id",
            String(128),
            nullable=False,
        ),
        Column("instrument_name", String(128)),
        Column("measure_name", String(128), nullable=False),
        Column("display_name", String(256)),
    )

    regression_values_t = Table(
        "regression_values",
        metadata,
        Column("regression_id", String(128), nullable=False),
        Column("measure_id", String(128), nullable=False),
        Column("figure_regression", String(256)),
        Column("figure_regression_small", String(256)),
        Column("pvalue_regression_male", Float()),
        Column("pvalue_regression_female", Float()),
    )

    tables = {
        "family": family_t,
        "person": person_t,
        "measure": measure_t,
        "instrument": instrument_t,
        "instrument_values": instrument_values_tables,
        "variable_browser": variable_browser_t,
        "regressions": regressions_t,
        "regression_values_t": regression_values_t,
    }

    metadata.create_all(duckdb_engine)

    return tables


def handle_value(val: Any) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, str):
        return f"'{val}'"
    return str(val)


def import_sqlite_into_duckdb(
    dbfile: str, sqlite_dbfile: str,
    sqlite_browser_dbfile: str,
    tables: dict[str, Any],
) -> None:
    """Import pheno data from legacy dbfile to duckdb dbfile."""
    con = duckdb.connect(dbfile)
    con.sql("INSTALL sqlite")
    con.sql("LOAD sqlite")
    con.sql(
        "INSERT INTO family "
        f"SELECT family_id FROM sqlite_scan('{sqlite_dbfile}', 'family')",
    )
    result = con.sql(
        "SELECT f.family_id, person_id, role, status, sex, sample_id "
        f"FROM sqlite_scan('{sqlite_dbfile}', 'person') as p "
        f"JOIN sqlite_scan('{sqlite_dbfile}', 'family') as f "
        "ON f.id = p.family_id",
    )
    rows = result.fetchall()
    for row in rows:
        values = list(row)
        role = Role.from_name(values[2])
        values[2] = role.value
        status = Status.from_name(values[3])
        values[3] = status.value
        sex = Sex.from_name(values[4])
        values[4] = sex.value
        values = [
            handle_value(val) for val in values
        ]
        values_str = ", ".join(values)
        con.sql(f"INSERT INTO person VALUES({values_str})")
    result = con.sql(
        "SELECT measure_id, db_column_name, measure_name, instrument_name, "
        "description, measure_type, individuals, default_filter, "
        "min_value, max_value, values_domain, rank "
        f"FROM sqlite_scan('{sqlite_dbfile}', 'measures') as m "
        f"JOIN sqlite_scan('{sqlite_dbfile}', 'instruments') as i "
        "ON m.instrument_id = i.id",
    )
    rows = result.fetchall()
    for row in rows:
        values = list(row)
        m_type = MeasureType.from_str(values[5])
        values[5] = m_type.value
        values = [
            handle_value(val) for val in values
        ]
        values_str = ", ".join(values)
        con.sql(f"INSERT INTO measure VALUES({values_str})")
    con.sql(
        "INSERT INTO instrument "
        "SELECT instrument_name, table_name "
        f"FROM sqlite_scan('{sqlite_dbfile}', 'instruments')",
    )
    if sqlite_browser_dbfile is not None:
        result = con.sql(
            "SELECT "
            "measure_id, instrument_name, measure_name, measure_type, "
            "description, values_domain, "
            "figure_distribution_small, figure_distribution "
            f"FROM sqlite_scan('{sqlite_browser_dbfile}', 'variable_browser')",
        )
        rows = result.fetchall()
        for row in rows:
            values = list(row)
            m_type = MeasureType.from_str(values[3])
            values[3] = m_type.value
            values = [handle_value(val) for val in values]
            values_str = ", ".join(values)
            con.sql(f"INSERT INTO variable_browser VALUES({values_str})")
        con.sql(
            "INSERT INTO regression SELECT * FROM "
            f"sqlite_scan('{sqlite_browser_dbfile}', 'regressions')",
        )
        con.sql(
            "INSERT INTO regression_values SELECT * FROM "
            f"sqlite_scan('{sqlite_browser_dbfile}', 'regression_values')",
        )
    for tbl_name in tables["instrument_values"].keys():

        result = con.sql(
            "DESCRIBE("
            f"SELECT * FROM sqlite_scan('{sqlite_dbfile}', "
            f"'{tbl_name}_measure_values')"
            ")",
        )
        rows = result.fetchall()
        table_cols = {}
        for idx, row in enumerate(rows):
            table_cols[row[0]] = idx

        result = con.sql(
            f"SELECT * FROM sqlite_scan('{sqlite_dbfile}', "
            f"'{tbl_name}_measure_values')",
        )
        rows = result.fetchall()
        for row in rows:
            values = list(row)
            sex = Sex.from_name(values[table_cols["sex"]])
            values[table_cols["sex"]] = sex.value
            status = Status.from_name(values[table_cols["status"]])
            values[table_cols["status"]] = status.value
            role = Role.from_name(values[table_cols["role"]])
            values[table_cols["role"]] = role.value
            values = [
                handle_value(val) for val in values
            ]
            values_str = ", ".join(values)
            con.sql(
                f"INSERT INTO {tbl_name}_measure_values VALUES({values_str})",
            )
