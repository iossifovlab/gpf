# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import yaml
import numpy as np
import pytest

from dae.genomic_resources.histogram import NumberHistogram, \
    NumberHistogramConfig, CategoricalHistogram, CategoricalHistogramConfig, \
    HistogramError, build_histogram_config


def test_histogram_simple_input() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 0, "max": 10},
        "number_of_bins": 10,
        "x_log_scale": False,
        "y_log_scale": True
    })
    assert config.y_log_scale

    hist = NumberHistogram(config)
    assert (hist.bins == np.arange(0, 11)).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])).all()

    for i in range(1, 11):
        hist.add_value(i)
    assert (hist.bars == np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 2])).all()

    hist.add_value(12)
    hist.add_value(-1)
    assert hist.out_of_range_bins == [1, 1]
    assert hist.min_value == -1
    assert hist.max_value == 12


def test_histogram_simple_input2() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 1, "max": 11},
        "number_of_bins": 10,
        "x_log_scale": False,
        "y_log_scale": True
    })
    assert config.y_log_scale

    hist = NumberHistogram(config)
    assert (hist.bins == np.arange(1, 12)).all()

    hist.add_value(1)
    assert (hist.bars == np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])).all()

    for i in range(2, 12):
        hist.add_value(i)
    assert (hist.bars == np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 2])).all()

    hist.add_value(13)
    hist.add_value(0)
    assert hist.out_of_range_bins == [1, 1]
    assert hist.min_value == 0
    assert hist.max_value == 13


def test_histogram_choose_bin_lin() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 1, "max": 11},
        "number_of_bins": 10,
        "x_log_scale": False,
        "y_log_scale": True
    })
    assert config.y_log_scale

    hist = NumberHistogram(config)

    assert hist.choose_bin_lin(1.0) == 0
    assert hist.choose_bin_lin(2.0) == 1
    assert hist.choose_bin_lin(10.0) == 9

    assert hist.choose_bin_lin(12.0) == -1
    assert hist.choose_bin_lin(0.5) == -2

    assert hist.choose_bin_lin(11.0) == 9


def test_histogram_log_scale() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 0, "max": 1000},
        "number_of_bins": 4,
        "x_log_scale": True,
        "y_log_scale": False,
        "x_min_log": 1
    })
    hist = NumberHistogram(config)
    assert (hist.bins == np.array([0, 1, 10, 100, 1000])).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0])).all()

    for i in [0.5, 2, 10, 200]:
        hist.add_value(i)
    assert (hist.bars == np.array([2, 1, 1, 1])).all()

    hist.add_value(2000)
    hist.add_value(-1)
    assert hist.out_of_range_bins == [1, 1]
    assert hist.min_value == -1
    assert hist.max_value == 2000


def test_histogram_choose_bin_log() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 0, "max": 1000},
        "number_of_bins": 4,
        "x_log_scale": True,
        "y_log_scale": False,
        "x_min_log": 1
    })
    hist = NumberHistogram(config)
    assert (hist.bins == np.array([0, 1, 10, 100, 1000])).all()

    assert hist.choose_bin_log(-1) == -2
    assert hist.choose_bin_log(1001) == -1

    assert hist.choose_bin_log(0) == 0
    assert hist.choose_bin_log(0.5) == 0

    assert hist.choose_bin_log(1.0) == 1
    assert hist.choose_bin_log(10.0) == 2
    assert hist.choose_bin_log(20.0) == 2
    assert hist.choose_bin_log(99.999) == 2

    assert hist.choose_bin_log(100.0) == 3
    assert hist.choose_bin_log(200.0) == 3
    assert hist.choose_bin_log(500.0) == 3
    assert hist.choose_bin_log(999.0) == 3
    assert hist.choose_bin_log(999.999) == 3

    assert hist.choose_bin_log(1000) == 3


def test_histogram_choose_bin_log2() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 0, "max": 1000},
        "number_of_bins": 5,
        "x_log_scale": True,
        "y_log_scale": False,
        "x_min_log": 0.1
    })
    hist = NumberHistogram(config)
    assert (hist.bins == np.array([0, 0.1, 1, 10, 100, 1000])).all()

    assert hist.choose_bin_log(-1) == -2
    assert hist.choose_bin_log(1001) == -1

    assert hist.choose_bin_log(0) == 0
    assert hist.choose_bin_log(0.05) == 0

    assert hist.choose_bin_log(0.1) == 1
    assert hist.choose_bin_log(0.5) == 1
    assert hist.choose_bin_log(0.9999) == 1

    assert hist.choose_bin_log(1.0) == 2

    assert hist.choose_bin_log(10.0) == 3
    assert hist.choose_bin_log(20.0) == 3
    assert hist.choose_bin_log(99.999) == 3

    assert hist.choose_bin_log(100.0) == 4
    assert hist.choose_bin_log(200.0) == 4
    assert hist.choose_bin_log(500.0) == 4
    assert hist.choose_bin_log(999.0) == 4
    assert hist.choose_bin_log(999.999) == 4

    assert hist.choose_bin_log(1000) == 4


def test_histogram_merge() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 0, "max": 10},
        "number_of_bins": 10,
        "x_log_scale": False,
        "y_log_scale": False
    })
    hist1 = NumberHistogram(
        config,
        bins=np.arange(0, 11),
        bars=np.array([0, 0, 0, 1, 0, 0, 0, 1, 0, 2])
    )
    hist2 = NumberHistogram(
        config,
        bins=np.arange(0, 11),
        bars=np.array([0, 0, 0, 0, 0, 1, 0, 1, 0, 0])
    )

    hist1.merge(hist2)
    assert (hist1.bars == np.array([0, 0, 0, 1, 0, 1, 0, 2, 0, 2])).all()


def test_histogram_serialize_deserialize() -> None:
    config = NumberHistogramConfig.from_dict({
        "type": "number",
        "view_range": {"min": 0, "max": 10},
        "number_of_bins": 10,
        "x_log_scale": False,
        "y_log_scale": False
    })
    hist1 = NumberHistogram(
        config,
        bins=np.arange(0, 11),
        bars=np.array([0, 0, 0, 1, 0, 0, 0, 1, 0, 2])
    )

    serialized = hist1.serialize()
    print(serialized)

    loaded = yaml.load(serialized, yaml.Loader)
    print(loaded)
    assert loaded["bins"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert loaded["bars"] == [0, 0, 0, 1, 0, 0, 0, 1, 0, 2]

    hist2 = NumberHistogram.deserialize(serialized)

    assert hist1.bins is not None and hist1.bars is not None
    assert hist2.bins is not None and hist2.bars is not None
    assert np.array_equal(hist2.bins, hist1.bins)
    assert np.array_equal(hist2.bars, hist1.bars)


def test_categorical_histogram() -> None:
    config = CategoricalHistogramConfig(["value1", "value2"])

    hist = CategoricalHistogram(config)
    assert set(hist.values.keys()) == set(["value1", "value2"])

    assert hist.values["value1"] == 0
    assert hist.values["value2"] == 0

    hist.add_value("value1")

    hist.add_value("value2")
    hist.add_value("value2")

    hist.add_value("value3")

    assert hist.values["value1"] == 1
    assert hist.values["value2"] == 2
    assert hist.values["value3"] == 1


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

    assert hist1.values["value1"] == 2
    assert hist1.values["value2"] == 2
    assert hist1.values["value4"] == 1

    assert hist2.values["value1"] == 0
    assert hist2.values["value2"] == 2
    assert hist2.values["value3"] == 2

    hist1.merge(hist2)
    assert hist1.values["value1"] == 2
    assert hist1.values["value2"] == 4
    assert hist1.values["value3"] == 2
    assert hist1.values["value4"] == 1


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
        "number_hist": {}
    },
    {
        "histogram": {"type": "number"}
    },
])
def test_build_number_histogram_config(conf: dict[str, Any]) -> None:
    hist_conf = build_histogram_config(conf)
    assert isinstance(hist_conf, NumberHistogramConfig)


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
