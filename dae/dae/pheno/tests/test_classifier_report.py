# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import duckdb
import pandas as pd

from dae.pheno.prepare.measure_classifier import MeasureClassifier


def test_fi1(
    fi1_df: pd.DataFrame,
    fi1_db: tuple[duckdb.DuckDBPyConnection, str],
) -> None:
    connection, table_name = fi1_db
    for col in fi1_df:
        report = MeasureClassifier.meta_measures(
            connection.cursor(), table_name, col,
        )
        assert (
            report.count_with_values
            == report.count_with_numeric_values
            + report.count_with_non_numeric_values
        )
        assert (
            report.count_total
            == report.count_with_values + report.count_without_values
        )
