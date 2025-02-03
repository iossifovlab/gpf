# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import numpy as np
import pytest

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    Histogram,
    NullHistogram,
    NumberHistogram,
)
from dae.pheno.common import InferenceConfig
from dae.pheno.prepare.measure_classifier import (
    Convertible,
    convert_to_numeric,
    convert_to_string,
    determine_histogram_type,
    inference_reference_impl,
    is_convertible_to_numeric,
    is_nan,
)


def test_is_nan() -> None:
    assert is_nan(float("nan")) is True
    assert is_nan(None) is True
    assert is_nan("") is True
    assert is_nan(1) is False
    assert is_nan(1.7) is False
    assert is_nan("sadkjhsfh") is False


def test_is_convertable_to_numeric() -> None:
    assert is_convertible_to_numeric(float("nan")) == Convertible.nan
    assert is_convertible_to_numeric(None) == Convertible.nan
    assert is_convertible_to_numeric("") == Convertible.nan
    assert is_convertible_to_numeric(True) == Convertible.non_numeric  # noqa: FBT003
    assert is_convertible_to_numeric(1234) == Convertible.numeric
    assert is_convertible_to_numeric(1.7) == Convertible.numeric
    assert is_convertible_to_numeric("1.7") == Convertible.numeric
    assert is_convertible_to_numeric("1234") == Convertible.numeric
    assert is_convertible_to_numeric("asdf") == Convertible.non_numeric


def test_convert_to_numeric() -> None:
    assert convert_to_numeric(123) == 123
    assert convert_to_numeric(1.7) == 1.7
    assert convert_to_numeric("123") == 123
    assert convert_to_numeric("1.7") == 1.7
    assert np.isnan(convert_to_numeric(None))
    assert np.isnan(convert_to_numeric(""))
    assert np.isnan(convert_to_numeric(True))  # noqa: FBT003


def test_convert_to_string() -> None:
    assert convert_to_string(123) == "123"
    assert convert_to_string("test") == "test"
    assert convert_to_string(None) is None
    assert convert_to_string(True) == "True"  # noqa: FBT003
    assert convert_to_string("") is None


def test_classify_default_continuous() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    ]))
    config = InferenceConfig()

    new_values, report = inference_reference_impl(values, config)

    assert determine_histogram_type(report, config) == NumberHistogram
    assert report.value_type is int

    assert new_values == [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    ]


def test_classify_default_ordinal() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, 5,
    ]))
    config = InferenceConfig()

    new_values, report = inference_reference_impl(values, config)

    assert determine_histogram_type(report, config) == CategoricalHistogram
    assert report.value_type is int

    assert new_values == [
        1, 2, 3, 4, 5,
    ]


def test_classify_default_categorical() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, "asdf",
    ]))
    config = InferenceConfig()

    new_values, report = inference_reference_impl(values, config)

    assert determine_histogram_type(report, config) == CategoricalHistogram
    assert report.value_type is str

    assert new_values == [
        "1", "2", "3", "4", "asdf",
    ]


def test_classify_default_limit_many_values_in_values_domain() -> None:
    values: list[str | None] = [f"id-{i}" for i in range(1, 100)]
    config = InferenceConfig()
    _, report = inference_reference_impl(values, config)
    assert len(report.values_domain.split(",")) == 20


def test_classify_all_none() -> None:
    values: list[str | None] = [
        None, None, None, None,
    ]
    config = InferenceConfig()

    new_values, report = inference_reference_impl(values, config)

    assert determine_histogram_type(report, config) == NullHistogram
    assert report.value_type is int

    assert new_values == [
        None, None, None, None,
    ]


@pytest.mark.parametrize(
    (
        "forced_histogram_type,forced_value_type,"
        "expected_histogram_type,expected_value_type,"
        "expected_values"
    ),
    [
        (
            None, None, CategoricalHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            "number", None, NumberHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            "categorical", None, CategoricalHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            "null", None, NullHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            None, "str", CategoricalHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            "number", "str", NumberHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            "categorical", "str", CategoricalHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            "null", "str", NullHistogram, str,
            ["1", "asdf", "ghjk", "k;jhlfjh"],
        ),
        (
            None, "int", CategoricalHistogram, int,
            [1, None, None, None],
        ),
        (
            "number", "int", NumberHistogram, int,
            [1, None, None, None],
        ),
        (
            "categorical", "int", CategoricalHistogram, int,
            [1, None, None, None],
        ),
        (
            "null", "int", NullHistogram, int,
            [1, None, None, None],
        ),
        (
            None, "float", CategoricalHistogram, float,
            [1, None, None, None],
        ),
        (
            "number", "float", NumberHistogram, float,
            [1, None, None, None],
        ),
        (
            "categorical", "float", CategoricalHistogram, float,
            [1, None, None, None],
        ),
        (
            "null", "float", NullHistogram, float,
            [1, None, None, None],
        ),
    ],
)
def test_inference_force_parameters(
    forced_histogram_type: str,
    forced_value_type: str,
    expected_histogram_type: type[Histogram],
    expected_value_type: type,
    expected_values: list[Any],
) -> None:
    values: list[str | None] = list(map(str, [
        1, "asdf", "ghjk", "k;jhlfjh",
    ]))
    config = InferenceConfig()
    config.histogram_type = forced_histogram_type
    config.value_type = forced_value_type

    new_values, report = inference_reference_impl(values, config)
    report.histogram_type = determine_histogram_type(report, config)

    assert report.histogram_type == expected_histogram_type
    assert report.value_type is expected_value_type

    assert new_values == expected_values
