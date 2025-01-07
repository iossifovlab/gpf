import argparse
import os
import sqlite3
from pathlib import Path

import duckdb
import pandas as pd

from dae.gene_profile.db import GeneProfileDBWriter
from dae.gpf_instance.gpf_instance import GPFInstance


def main(
    gpf_instance: GPFInstance | None = None,
    argv: list[str] | None = None,
) -> None:
    """Simple gpdb converter from sqlite to duckdb."""
    # flake8: noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    description = "Gene profiles database converter from sqlite to duckdb"
    parser = argparse.ArgumentParser(description=description)

    dae_db_dir = Path(os.getenv("DAE_DB_DIR", "./"))

    default_dbfile = str(dae_db_dir / "gpdb")
    parser.add_argument("--dbfile", default=default_dbfile)

    default_output = str(dae_db_dir / "gpdb.duckdb")
    parser.add_argument("--output", default=default_output)

    args = parser.parse_args(argv)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    # pylint: disable=protected-access, invalid-name
    config = gpf_instance._gene_profile_config  # noqa: SLF001

    assert config is not None, "No GP configuration found."

    gpdb = GeneProfileDBWriter(
        config.to_dict(),
        args.output,
    )

    table_name = "gene_profile"
    query = f"SELECT * from {table_name}"  # noqa: S608

    conn = sqlite3.connect(database=args.dbfile)

    df = pd.read_sql(query, conn)  # noqa: F841

    with duckdb.connect(f"{gpdb.dbfile}") as connection:
        connection.execute("INSERT INTO gene_profile SELECT * FROM df")
