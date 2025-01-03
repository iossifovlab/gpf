import argparse
import os
import sqlite3

import duckdb
import pandas as pd

from dae.gene_profile.db import GeneProfileDBWriter
from dae.gpf_instance.gpf_instance import GPFInstance


def main(
    gpf_instance: GPFInstance | None = None,
    argv: list[str] | None = None,
) -> None:
    """Entry point for the generate GP script."""
    # flake8: noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    description = "Generate gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "gpdb")
    parser.add_argument("--dbfile", default=default_dbfile)

    args = parser.parse_args(argv)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    # pylint: disable=protected-access, invalid-name
    config = gpf_instance._gene_profile_config  # noqa: SLF001

    assert config is not None, "No GP configuration found."

    gpdb = GeneProfileDBWriter(
        config.to_dict(),
        os.path.join(os.getenv("DAE_DB_DIR", "./"), "gpdb.duckdb"),
    )

    table_name = "gene_profile"
    query = f"SELECT * from {table_name}"  # noqa: S608

    conn = sqlite3.connect(database=args.dbfile)

    df = pd.read_sql(query, conn)

    df.to_csv("gpdb_data.csv", index=False)

    with duckdb.connect(f"{gpdb.dbfile}") as connection:
        connection.execute('COPY gene_profile FROM "gpdb_data.csv"')
