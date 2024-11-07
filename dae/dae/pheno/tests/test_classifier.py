# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.pheno.common import InferenceConfig, MeasureType
from dae.pheno.prepare.measure_classifier import classification_reference_impl


def test_classify_default_continuous() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    ]))
    config = InferenceConfig()

    new_values, report = classification_reference_impl(values, config)

    assert report.measure_type == MeasureType.continuous  # type: ignore

    assert new_values == [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    ]


def test_classify_default_ordinal() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, 5,
    ]))
    config = InferenceConfig()

    new_values, report = classification_reference_impl(values, config)

    assert report.measure_type == MeasureType.ordinal  # type: ignore

    assert new_values == [
        1, 2, 3, 4, 5,
    ]


def test_classify_default_categorical() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, "asdf",
    ]))
    config = InferenceConfig()

    new_values, report = classification_reference_impl(values, config)

    assert report.measure_type == MeasureType.categorical  # type: ignore

    assert new_values == [
        "1", "2", "3", "4", "asdf",
    ]


def test_classify_force_str() -> None:
    values: list[str | None] = list(map(str, [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    ]))
    config = InferenceConfig()
    config.measure_type = "raw"

    new_values, report = classification_reference_impl(values, config)

    assert report.measure_type == MeasureType.raw  # type: ignore

    assert new_values == values


def test_classify_force_numeric() -> None:
    values: list[str | None] = list(map(str, [
        1, "asdf", "ghjk", "k;jhlfjh",
    ]))
    config = InferenceConfig()
    config.measure_type = "continuous"

    new_values, report = classification_reference_impl(values, config)

    assert report.measure_type == MeasureType.continuous  # type: ignore

    assert new_values == [1, None, None, None]


def test_classify_force_numeric_no_numeric_values() -> None:
    values: list[str | None] = list(map(str, [
        "asdf", "ghjk", "k;jhlfjh",
    ]))
    config = InferenceConfig()
    config.measure_type = "continuous"

    with pytest.raises(ValueError, match=r"Measure is set as numeric.+"):
        classification_reference_impl(values, config)
