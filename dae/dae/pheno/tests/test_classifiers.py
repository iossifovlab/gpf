# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
import pandas as pd

from dae.pheno.prepare.measure_classifier import MeasureClassifier
from dae.pheno.common import MeasureType, default_config


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
    fi1_df: pd.DataFrame,
    measure: str,
    expected_type: MeasureType
) -> None:
    values = fi1_df[measure]
    classifier = MeasureClassifier(default_config())
    classifier_report = MeasureClassifier.meta_measures(values)
    measure_type = classifier.classify(classifier_report)

    assert measure_type == expected_type
