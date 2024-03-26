# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from box import Box
import pandas as pd
import duckdb

from dae.pheno.prepare.measure_classifier import MeasureClassifier
from dae.pheno.common import default_config, MeasureType
from dae.pheno.prepare.pheno_prepare import PrepareVariables


def test_fake_background_classify(
    fake_background_df: pd.DataFrame,
    fake_background_db: tuple[duckdb.DuckDBPyConnection, str]
) -> None:

    connection, table_name = fake_background_db
    columns = list(fake_background_df.columns)
    for col in columns[1:]:
        classifier = MeasureClassifier(default_config())
        classifier_report = MeasureClassifier.meta_measures(
            connection, table_name, col
        )
        measure_type = classifier.classify(classifier_report)

        assert measure_type in {
            MeasureType.text,
            MeasureType.raw,
            MeasureType.categorical,
            MeasureType.ordinal
        }
