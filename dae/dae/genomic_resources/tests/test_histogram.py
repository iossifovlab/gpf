# pylint: disable=W0621,C0114,C0116,W0212,W0613

import yaml
import numpy as np

from dae.genomic_resources.histogram import Histogram


def test_histogram_simple_input():
    config = {
        "score": "test",
        "bins": 10,
        "min": 0,
        "max": 10,
        "x_scale": "linear",
        "y_scale": "linear"
    }
    hist = Histogram(config)
    assert (hist.bins == np.arange(0, 11)).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])).all()

    for i in range(1, 11):
        hist.add_value(i)
    assert (hist.bars == np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 2])).all()

    hist.add_value(12)
    hist.add_value(-1)
    assert (hist.bars == np.array([2, 1, 1, 1, 1, 1, 1, 1, 1, 3])).all()


def test_histogram_log_scale():
    config = {
        "score": "test",
        "bins": 4,
        "min": 0,
        "max": 1000,
        "x_scale": "log",
        "y_scale": "linear",
        "x_min_log": 1
    }
    hist = Histogram(config)
    assert (hist.bins == np.array([0, 1, 10, 100, 1000])).all()

    hist.add_value(0)
    assert (hist.bars == np.array([1, 0, 0, 0])).all()

    for i in [0.5, 2, 10, 200]:
        hist.add_value(i)
    assert (hist.bars == np.array([2, 1, 1, 1])).all()

    hist.add_value(2000)
    hist.add_value(-1)
    assert (hist.bars == np.array([3, 1, 1, 2])).all()


def test_histogram_merge():
    config = {
        "score": "test",
        "bins": 10,
        "x_min": 0,
        "x_max": 10,
        "x_scale": "linear",
        "y_scale": "linear"
    }
    hist1 = Histogram(
        config,
        bins=np.arange(0, 11),
        bars=np.array([0, 0, 0, 1, 0, 0, 0, 1, 0, 2])
    )
    hist2 = Histogram(
        config,
        bins=np.arange(0, 11),
        bars=np.array([0, 0, 0, 0, 0, 1, 0, 1, 0, 0])
    )

    hist1.merge(hist2)
    assert (hist1.bars == np.array([0, 0, 0, 1, 0, 1, 0, 2, 0, 2])).all()


def test_histogram_serialize_deserialize():
    config = {
        "score": "test",
        "bins": 10,
        "x_min": 0,
        "x_max": 10,
        "x_scale": "linear",
        "y_scale": "linear"
    }
    hist1 = Histogram(
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

    hist2 = Histogram.deserialize(serialized)

    assert np.array_equal(hist2.bins, hist1.bins)
    assert np.array_equal(hist2.bars, hist1.bars)
