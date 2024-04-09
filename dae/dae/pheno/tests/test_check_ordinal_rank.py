# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from typing import Generator, Callable
import pandas as pd
import pytest
import duckdb
from dae.pheno.common import default_config, MeasureType
from dae.pheno.prepare.measure_classifier import MeasureClassifier
from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno.db import safe_db_name


@pytest.fixture(scope="function")
def db_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect("memory")


@pytest.fixture(scope="function")
def db_builder(db_connection: duckdb.DuckDBPyConnection) -> Generator[
    Callable,
    None,
    None
]:
    table_name = "tmp"

    def builder(df: pd.DataFrame) -> str:
        db_connection.sql(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        print(db_connection.sql("select 'i1.m4' from tmp"))
        return table_name
    yield builder

    db_connection.sql(f"DROP TABLE {table_name}")


def test_fake_phenotype_data_ordinal_m4(
    fake_phenotype_data: PhenotypeStudy,
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    measure_id = "i1.m4"
    df = fake_phenotype_data.get_people_measure_values_df([measure_id])
    df.rename(columns=safe_db_name, inplace=True)
    measure_id = safe_db_name("i1.m4")
    rank = len(df[measure_id].unique())
    assert rank == 9
    assert len(df) == 195

    table_name = db_builder(df)

    measure_conf = default_config()
    classifier = MeasureClassifier(measure_conf)
    report = classifier.meta_measures(
        db_connection.cursor(), table_name, measure_id
    )
    assert classifier.classify(report) == MeasureType.ordinal
