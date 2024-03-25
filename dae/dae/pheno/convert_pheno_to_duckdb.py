from typing import Any, Union, Optional

import duckdb

from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Float, \
    ForeignKey, or_, func, desc, Sequence
from sqlalchemy.sql import select, Select, text
from sqlalchemy.sql.schema import UniqueConstraint

from dae.pheno.db import PhenoDb
from dae.pheno.common import MeasureType
from dae.variants.attributes import Sex, Status, Role


def create_sqlite_phenodb(
    dbfile: str, browser_dbfile: Optional[str] = None
) -> PhenoDb:
    db = PhenoDb(dbfile, browser_dbfile)
    db.build()
    return db


def build_instrument_values_tables(metadata: MetaData, sqlite_db: PhenoDb):
    instrument_values_tables: dict[str, Table] = {}
    query = select(
        sqlite_db.instruments.c.instrument_name,
        sqlite_db.instruments.c.table_name
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
        sqlite_db.instruments.c.instrument_name
    ).join(sqlite_db.instruments)
    with sqlite_db.pheno_engine.connect() as connection:
        results = connection.execute(query)
        measure_columns: dict[str, Column] = {}
        for result_row in results:
            instrument_measures[result_row.instrument_name].append(
                result_row.measure_id
            )
            if MeasureType.is_numeric(result_row.measure_type):
                column_type: Union[Float, String] = Float()
            else:
                column_type = String(127)
            measure_columns[result_row.measure_id] = \
                Column(
                    f"{result_row.db_column_name}",
                    column_type, nullable=True
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
                    "family_id", String(64), nullable=False
                ),
                Column("role", Integer(), nullable=False),
                Column(
                    "status",
                    Integer(),
                    nullable=False,
                    default=1
                ),
                Column("sex", Integer(), nullable=False),
                *cols,
                extend_existing=True
            )
    return instrument_values_tables


def create_duckdb_dbfile(dbfile: str, sqlite_db: PhenoDb) -> dict[str, Any]:
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
        metadata, sqlite_db
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
        "regression_values_t": regression_values_t
    }


    metadata.create_all(duckdb_engine)

    return tables


def handle_value(val):
    if val is None:
        return "NULL"
    if isinstance(val, str):
        return f"'{val}'"
    return str(val)


def import_sqlite_into_duckdb(
    dbfile: str, sqlite_dbfile: str,
    sqlite_browser_dbfile: str,
    tables: dict[str, Any]
) -> None:
    con = duckdb.connect(dbfile)
    con.sql("INSTALL sqlite")
    con.sql("LOAD sqlite")
    con.sql(
        "INSERT INTO family "
        f"SELECT family_id FROM sqlite_scan('{sqlite_dbfile}', 'family')"
    )
    result = con.sql(
        "SELECT f.family_id, person_id, role, status, sex, sample_id "
        f"FROM sqlite_scan('{sqlite_dbfile}', 'person') as p "
        f"JOIN sqlite_scan('{sqlite_dbfile}', 'family') as f "
        "ON f.id = p.family_id"
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
        "ON m.instrument_id = i.id"
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
        f"FROM sqlite_scan('{sqlite_dbfile}', 'instruments')"
    )
    if sqlite_browser_dbfile is not None:
        result = con.sql(
            "SELECT "
            "measure_id, instrument_name, measure_name, measure_type, "
            "description, values_domain, "
            "figure_distribution_small, figure_distribution "
            f"FROM sqlite_scan('{sqlite_browser_dbfile}', 'variable_browser')"
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
            f"sqlite_scan('{sqlite_browser_dbfile}', 'regressions')"
        )
        con.sql(
            "INSERT INTO regression_values SELECT * FROM "
            f"sqlite_scan('{sqlite_browser_dbfile}', 'regression_values')"
        )
    for tbl_name in tables["instrument_values"].keys():

        result = con.sql(
            "DESCRIBE("
            f"SELECT * FROM sqlite_scan('{sqlite_dbfile}', "
            f"'{tbl_name}_measure_values')"
            ")"
        )
        rows = result.fetchall()
        table_cols = {}
        for idx, row in enumerate(rows):
            table_cols[row[0]] = idx

        result = con.sql(
            f"SELECT * FROM sqlite_scan('{sqlite_dbfile}', "
            f"'{tbl_name}_measure_values')"
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
                f"INSERT INTO {tbl_name}_measure_values VALUES({values_str})"
            )
