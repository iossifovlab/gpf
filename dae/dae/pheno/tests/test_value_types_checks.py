# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from typing import Generator, Callable
import numpy as np
import pandas as pd
import duckdb
import pytest

from dae.pheno.common import MeasureType, default_config
from dae.pheno.prepare.measure_classifier import MeasureClassifier


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
        return table_name
    yield builder

    db_connection.sql(f"DROP TABLE {table_name}")


def test_classifier_non_numeric(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": ["1", "2", "3", "4.4", "a"]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    print(res)

    assert res.count_with_values == 5
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 4
    assert res.count_with_non_numeric_values == 1


def test_classifier_nan(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": [" ", None, np.nan, "1", "2.2"]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    print(res)

    assert res.count_with_values == 3
    assert res.count_without_values == 2
    assert res.count_with_numeric_values == 2
    assert res.count_with_non_numeric_values == 1


def test_classifier_float(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": [" ", None, np.nan, 1, 2.2]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    print(res)

    assert res.count_with_values == 3
    assert res.count_without_values == 2
    assert res.count_with_numeric_values == 2
    assert res.count_with_non_numeric_values == 1


def test_classifier_all_float(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": [3.3, 1, 2.2]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    print(res)

    assert res.count_with_values == 3
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 3
    assert res.count_with_non_numeric_values == 0


def test_classifier_all_float_again(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": [3.3, 1, 2.2, 3.3, 1, 1]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    assert res.count_with_values == 6
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 6
    assert res.count_with_non_numeric_values == 0


def test_classifier_all_bool(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": [True, False, True]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    assert res.count_with_values == 3
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 3
    assert res.count_with_non_numeric_values == 0


def test_classifier_bool_and_nan(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": [True, False, True, np.nan, None, " "]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    res = MeasureClassifier.meta_measures(cursor, table_name, "test")
    print(res)
    assert res.count_with_values == 4
    assert res.count_without_values == 2
    assert res.count_with_numeric_values == 0
    assert res.count_with_non_numeric_values == 4


def test_should_convert_to_numeric_cutoff(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": ["1", "2", "1", "1", "1", "1", "2", "2", "a"]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    report = MeasureClassifier.meta_measures(cursor, table_name, "test")

    config = default_config()
    config.classification.min_individuals = 1
    config.classification.ordinal.min_rank = 2

    classifier = MeasureClassifier(config)
    measure_type = classifier.classify(report)
    assert measure_type == MeasureType.categorical

    config.classification.non_numeric_cutoff = 0.2
    classifier = MeasureClassifier(config)
    measure_type = classifier.classify(report)
    assert measure_type == MeasureType.ordinal


def test_classify_minus_values(
    db_connection: duckdb.DuckDBPyConnection,
    db_builder: Callable
) -> None:
    df = pd.DataFrame({"test": ["-", "-", "-", np.nan, None, " ", "-"]})
    table_name = db_builder(df)
    cursor = db_connection.cursor()

    report = MeasureClassifier.meta_measures(cursor, table_name, "test")
    assert report.count_with_numeric_values == 0
    assert report.count_without_values == 2
    assert report.count_with_non_numeric_values == 5
