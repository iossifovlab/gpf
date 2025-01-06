# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import pytest

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    Histogram,
    NullHistogram,
    NumberHistogram,
)
from dae.pheno.common import InferenceConfig
from dae.pheno.prepare.measure_classifier import (
    determine_histogram_type,
    inference_reference_impl,
)


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
