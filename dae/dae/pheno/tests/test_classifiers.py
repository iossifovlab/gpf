# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import duckdb
import pytest

from dae.pheno.common import MeasureType, default_config
from dae.pheno.prepare.measure_classifier import MeasureClassifier


@pytest.mark.parametrize(
    "measure, expected_type",
    [
        # Continuous, numeric values only
        ("m1", MeasureType.continuous),
        ("m2", MeasureType.continuous),
        ("m3", MeasureType.continuous),
        # Ordinal, numeric values only
        ("m4", MeasureType.ordinal),
        # Categorical, non-numeric values only
        ("m5", MeasureType.categorical),
        # Raw, all values are NaN
        ("m6", MeasureType.raw),
        # Continuous, non-numeric values below threshold
        ("m7", MeasureType.continuous),
        # Ordinal, non-numeric values below threshold
        ("m8", MeasureType.ordinal),
        # Continuous, non-numeric values above threshold
        ("m9", MeasureType.raw),
    ],
)
def test_fi1(
    fi1_db: tuple[duckdb.DuckDBPyConnection, str],
    measure: str,
    expected_type: MeasureType,
) -> None:
    connection, table_name = fi1_db
    classifier = MeasureClassifier(default_config().classification)
    classifier_report = MeasureClassifier.meta_measures(
        connection.cursor(),
        table_name, measure,
    )
    measure_type = classifier.classify(classifier_report)

    assert measure_type == expected_type
