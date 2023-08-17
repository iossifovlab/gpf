# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, Optional

import pytest

from dae.genomic_resources.histogram import \
    CategoricalHistogram, CategoricalHistogramConfig, \
    HistogramError, build_histogram_config


def test_categorical_histogram() -> None:
    config = CategoricalHistogramConfig(["value1", "value2"])

    hist = CategoricalHistogram(config)

    assert set(hist.bars.keys()) == set(["value1", "value2"])

    assert hist.bars["value1"] == 0
    assert hist.bars["value2"] == 0

    hist.add_value("value1")

    hist.add_value("value2")
    hist.add_value("value2")

    hist.add_value("value3")

    assert hist.bars["value1"] == 1
    assert hist.bars["value2"] == 2
    assert hist.bars["value3"] == 1


def test_categorical_histogram_add_value_raises() -> None:
    config = CategoricalHistogramConfig.default_config()

    hist = CategoricalHistogram(config)
    with pytest.raises(HistogramError):
        for i in range(101):
            hist.add_value(f"value{i}")


def test_categorical_histogram_merge() -> None:
    config = CategoricalHistogramConfig(["value1", "value2"])

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

    assert hist1.bars["value1"] == 2
    assert hist1.bars["value2"] == 2
    assert hist1.bars["value4"] == 1

    assert hist2.bars["value1"] == 0
    assert hist2.bars["value2"] == 2
    assert hist2.bars["value3"] == 2

    hist1.merge(hist2)
    assert hist1.bars["value1"] == 2
    assert hist1.bars["value2"] == 4
    assert hist1.bars["value3"] == 2
    assert hist1.bars["value4"] == 1


def test_categorical_histogram_merge_raises() -> None:
    config = CategoricalHistogramConfig.default_config()

    hist1 = CategoricalHistogram(config)
    for i in range(50):
        hist1.add_value(f"value{i}")
    hist2 = CategoricalHistogram(config)
    for i in range(51):
        hist2.add_value(f"value{i+50}")
    with pytest.raises(HistogramError):
        hist1.merge(hist2)


@pytest.mark.parametrize("conf", [
    {
        "categorical_hist": {}
    },
    {
        "histogram": {"type": "categorical"}
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
        value_order: Optional[list[str]],
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig()
    hist = CategoricalHistogram(hist_conf)

    hist.add_value("2")
    hist.add_value("1")
    hist.add_value("1")

    assert hist.bars == expected_bars


@pytest.mark.parametrize("value_order, expected_bars", [
    (None, {"1": 2, "2": 1}),
    (["2", "1"], {"2": 1, "1": 2}),
])
def test_categorical_histogram_merge_values_order(
        value_order: Optional[list[str]],
        expected_bars: dict[str, int]) -> None:
    hist_conf = CategoricalHistogramConfig()
    hist = CategoricalHistogram(hist_conf)

    hist.add_value("2")
    hist.add_value("1")

    hist2 = CategoricalHistogram(hist_conf)
    hist2.add_value("1")

    hist.merge(hist2)

    assert hist.bars == expected_bars
