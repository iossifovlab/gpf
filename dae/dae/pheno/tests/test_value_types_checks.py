# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import numpy as np
import pandas as pd

from dae.pheno.common import MeasureType, default_config
from dae.pheno.prepare.measure_classifier import MeasureClassifier


def test_classifier_non_numeric() -> None:
    values = pd.Series(data=["1", "2", "3", "4.4", "a"])

    res = MeasureClassifier.meta_measures(values)
    print(res)

    assert res.count_with_values == 5
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 4
    assert res.count_with_non_numeric_values == 1

    res = MeasureClassifier.convert_to_numeric(values)
    print(res)
    print(res.dtype)


def test_classifier_nan() -> None:
    values = pd.Series(data=[" ", None, np.nan, "1", "2.2"])
    res = MeasureClassifier.meta_measures(values)
    print(res)

    assert res.count_with_values == 2
    assert res.count_without_values == 3
    assert res.count_with_numeric_values == 2
    assert res.count_with_non_numeric_values == 0

    res = MeasureClassifier.convert_to_numeric(values)
    print(res)
    print(res.dtype)


def test_classifier_float() -> None:
    values = pd.Series(data=[" ", None, np.nan, 1, 2.2])
    res = MeasureClassifier.meta_measures(values)
    print(res)

    assert res.count_with_values == 2
    assert res.count_without_values == 3
    assert res.count_with_numeric_values == 2
    assert res.count_with_non_numeric_values == 0

    res = MeasureClassifier.convert_to_numeric(values)
    print(res)
    print(res.dtype)


def test_classifier_all_float() -> None:
    values = pd.Series(data=[3.3, 1, 2.2])
    res = MeasureClassifier.meta_measures(values)
    print(res)

    assert res.count_with_values == 3
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 3
    assert res.count_with_non_numeric_values == 0

    res = MeasureClassifier.convert_to_numeric(values)
    print(res)
    print(res.dtype)


def test_classifier_all_float_again() -> None:
    values = pd.Series(data=[3.3, 1, 2.2, 3.3, 1, 1])
    res = MeasureClassifier.meta_measures(values)
    assert res.count_with_values == 6
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 6
    assert res.count_with_non_numeric_values == 0

    res = MeasureClassifier.convert_to_numeric(values)
    print(res)
    print(res.dtype)


def test_classifier_all_bool() -> None:
    values = pd.Series(data=[True, False, True])
    res = MeasureClassifier.meta_measures(values)
    assert res.count_with_values == 3
    assert res.count_without_values == 0
    assert res.count_with_numeric_values == 0
    assert res.count_with_non_numeric_values == 3

    res = MeasureClassifier.convert_to_numeric(values)
    assert res.dtype == np.float64


def test_classifier_bool_and_nan() -> None:
    values = pd.Series(data=[True, False, True, np.nan, None, " "])
    res = MeasureClassifier.meta_measures(values)
    print(res)
    assert res.count_with_values == 3
    assert res.count_without_values == 3
    assert res.count_with_numeric_values == 0
    assert res.count_with_non_numeric_values == 3

    res = MeasureClassifier.convert_to_numeric(values)
    print(res)
    print(res.dtype)


def test_should_convert_to_numeric_cutoff() -> None:
    values = pd.Series(data=["1", "2", "1", "1", "1", "1", "2", "2", "a"])
    report = MeasureClassifier.meta_measures(values)

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


def test_clasify_minus_values() -> None:
    values = pd.Series(data=["-", "-", "-", np.nan, None, " ", "-"])
    report = MeasureClassifier.meta_measures(values)
    assert report.count_with_numeric_values == 0
    assert report.count_without_values == 3
    assert report.count_with_non_numeric_values == 4
