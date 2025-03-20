# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import pytest

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
    HistogramError,
    build_histogram_config,
)


def test_categorical_histogram() -> None:
    config = CategoricalHistogramConfig(
        value_order=["value1", "value2", "value3"])

    hist = CategoricalHistogram(config)

    assert set(hist.display_values.keys()) == {"value1", "value2", "value3"}

    assert hist.display_values["value1"] == 0
    assert hist.display_values["value2"] == 0

    hist.add_value("value1")

    hist.add_value("value2")
    hist.add_value("value2")

    hist.add_value("value3")

    assert hist.display_values["value1"] == 1
    assert hist.display_values["value2"] == 2
    assert hist.display_values["value3"] == 1


def test_categorical_histogram_default_config_add_value_raises() -> None:
    config = CategoricalHistogramConfig.default_config()

    hist = CategoricalHistogram(config)
    assert hist.is_default

    for i in range(100):
        hist.add_value(f"value{i}")
    with pytest.raises(HistogramError):
        hist.add_value("value100")


def test_categorical_histogram_add_value_does_not_raise() -> None:
    config = CategoricalHistogramConfig()

    hist = CategoricalHistogram(config)
    assert not hist.is_default

    for i in range(100):
        hist.add_value(f"value{i}")
    hist.add_value("value100")


def test_categorical_histogram_merge() -> None:
    config = CategoricalHistogramConfig(
        value_order=["value1", "value2", "value3", "value4"])

    hist1 = CategoricalHistogram(config)

    hist2 = CategoricalHistogram(config)

    hist1.add_value("value1")
    hist1.add_value("value1")
    hist1.add_value("value2")
    hist1.add_value("value2")
    hist1.add_value("value4")

    hist2.add_value("value2")
    hist2.add_value("value2")
    hist2.add_value("value3")
    hist2.add_value("value3")

    assert hist1.display_values["value1"] == 2
    assert hist1.display_values["value2"] == 2
    assert hist1.display_values["value4"] == 1

    assert hist2.display_values["value1"] == 0
    assert hist2.display_values["value2"] == 2
    assert hist2.display_values["value3"] == 2

    hist1.merge(hist2)
    assert hist1.display_values["value1"] == 2
    assert hist1.display_values["value2"] == 4
    assert hist1.display_values["value3"] == 2
    assert hist1.display_values["value4"] == 1


def test_categorical_histogram_merge_raises() -> None:
    config = CategoricalHistogramConfig.default_config()

    hist1 = CategoricalHistogram(config)
    for i in range(50):
        hist1.add_value(f"value{i}")
    hist2 = CategoricalHistogram(config)
    for i in range(51):
        hist2.add_value(f"value{i + 50}")
    with pytest.raises(HistogramError):
        hist1.merge(hist2)


@pytest.mark.parametrize("conf", [
    {
        "histogram": {"type": "categorical"},
    },
])
def test_build_categorical_histogram_config(conf: dict[str, Any]) -> None:
    hist_conf = build_histogram_config(conf)
    assert isinstance(hist_conf, CategoricalHistogramConfig)


@pytest.mark.parametrize("value_order, expected_bars", [
    (None, {"1": 2, "2": 1}),
    (["2", "1"], {"2": 1, "1": 2}),
])
def test_categorical_histogram_values_order(
        value_order: list[str | int] | None,
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig(value_order=value_order)
    hist = CategoricalHistogram(hist_conf)

    hist.add_value("2")
    hist.add_value("1")
    hist.add_value("1")

    assert hist.display_values == expected_bars


@pytest.mark.parametrize("value_order, expected_bars", [
    (None, {"1": 2, "2": 1}),
    (["2", "1"], {"2": 1, "1": 2}),
])
def test_categorical_histogram_merge_values_order(
        value_order: list[str | int] | None,
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig(value_order=value_order)
    hist = CategoricalHistogram(hist_conf)

    hist.add_value("2")
    hist.add_value("1")

    hist2 = CategoricalHistogram(hist_conf)
    hist2.add_value("1")

    hist.merge(hist2)

    assert hist.display_values == expected_bars


@pytest.mark.parametrize("displayed_values_count, expected_bars", [
    (None, {"1": 1, "2": 1, "3": 1}),
    (3, {"1": 1, "2": 1, "3": 1}),
    (2, {"1": 1, "2": 1, "Other Values": 1}),
])
def test_categorical_histogram_number_of_displayed_values(
        displayed_values_count: int | None,
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig(
        displayed_values_count=displayed_values_count)
    hist = CategoricalHistogram(hist_conf)

    hist.add_value("1")
    hist.add_value("2")
    hist.add_value("3")

    assert hist.display_values == expected_bars


def populate_categorical_histogram(hist: CategoricalHistogram) -> None:
    for i in range(1, 11):
        for _ in range(i * 10):
            hist.add_value(str(i))


@pytest.mark.parametrize("displayed_values_count, expected_bars", [
    (3, {"10": 100, "9": 90, "8": 80, "Other Values": 280}),
    (4, {"10": 100, "9": 90, "8": 80, "7": 70, "Other Values": 210}),
    (5, {"10": 100, "9": 90, "8": 80, "7": 70, "6": 60, "Other Values": 150}),
    (2, {"10": 100, "9": 90, "Other Values": 360}),
])
def test_categorical_histogram_number_of_displayed_values_populated(
        displayed_values_count: int | None,
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig(
        displayed_values_count=displayed_values_count)
    hist = CategoricalHistogram(hist_conf)
    populate_categorical_histogram(hist)

    assert hist.display_values == expected_bars


def populate_categorical_histogram_with_int(
    hist: CategoricalHistogram,
) -> None:
    for i in range(1, 11):
        for _ in range(i * 10):
            hist.add_value(i)


@pytest.mark.parametrize("displayed_values_count, expected_bars", [
    (3, {10: 100, 9: 90, 8: 80, "Other Values": 280}),
])
def test_categorical_histogram_number_of_displayed_values_int_populated(
        displayed_values_count: int | None,
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig(
        displayed_values_count=displayed_values_count)
    hist = CategoricalHistogram(hist_conf)
    populate_categorical_histogram_with_int(hist)

    assert hist.display_values == expected_bars
