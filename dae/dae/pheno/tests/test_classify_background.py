# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import duckdb
import pandas as pd

from dae.pheno.common import MeasureType, default_config
from dae.pheno.prepare.measure_classifier import MeasureClassifier


def test_fake_background_classify(
    fake_background_df: pd.DataFrame,
    fake_background_db: tuple[duckdb.DuckDBPyConnection, str],
) -> None:

    connection, table_name = fake_background_db
    columns = list(fake_background_df.columns)
    for col in columns[1:]:
        classifier = MeasureClassifier(default_config().classification)
        classifier_report = MeasureClassifier.meta_measures(
            connection, table_name, col,
        )
        measure_type = classifier.classify(classifier_report)

        assert measure_type in {
            MeasureType.text,
            MeasureType.raw,
            MeasureType.categorical,
            MeasureType.ordinal,
        }
