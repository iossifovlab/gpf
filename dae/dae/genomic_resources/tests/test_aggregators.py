# pylint: disable=W0621,C0114,C0116,W0212,W0613

import numpy
from dae.genomic_resources.aggregators import (
    ConcatAggregator, MinAggregator,
    MaxAggregator, MeanAggregator,
    ModeAggregator, MedianAggregator,
    JoinAggregator, ListAggregator,
    DictAggregator
)


def test_concat_aggregator():
    values = ["a", "b", "c", "d"]
    agg = ConcatAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == "abcd"


def test_min_aggregator():
    values = [5, 6, 1, 2, 7]
    agg = MinAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == 1


def test_min_aggregator_string():
    values = ["asdf", "ghjk", "zab", "zob"]
    agg = MinAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == "asdf"


def test_max_aggregator():
    values = [5, 6, 1, 2, 7]
    agg = MaxAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == 7


def test_max_aggregator_string():
    values = ["asdf", "ghjk", "zab", "zob"]
    agg = MaxAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == "zob"


def test_mean_aggregator():
    values = [1, 2, 3, 4]
    agg = MeanAggregator()
    for val in values:
        agg.add(val)

    assert numpy.isclose(agg.get_final(), 2.5)


def test_median_aggregator_even():
    values = [2, 3, 4, 1]
    agg = MedianAggregator()
    for val in values:
        agg.add(val)

    assert numpy.isclose(agg.get_final(), 2.5)


def test_median_aggregator_odd():
    values = [2, 3, 4, 1, 5]
    agg = MedianAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == 3


def test_median_aggregator_string_even():
    values = ["a", "c", "b", "d"]
    agg = MedianAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == "bc"


def test_median_aggregator_string_odd():
    values = ["a", "c", "b", "d", "f"]
    agg = MedianAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == "c"


def test_mode_aggregator():
    values = [1, 2, 3, 1, 5, 6, 6, 1]
    agg = ModeAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == 1


def test_mode_aggregator_multimode():
    values = [6, 2, 3, 6, 5, 1, 1, 6, 1, 4, 4, 4]
    agg = ModeAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == 1


def test_join_aggregator():
    values = [1, 2, 3, 4, 5]
    agg = JoinAggregator(", ")
    for val in values:
        agg.add(val)

    assert agg.get_final() == "1, 2, 3, 4, 5"


def test_aggregator_used_counts():
    values = [1, 2, 3, None, None, 4, 5]
    agg = MinAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_used_count() == 5
    assert agg.get_total_count() == 7
    agg.clear()
    assert agg.get_used_count() == 0
    assert agg.get_total_count() == 0

    agg.add("asdf")
    agg.add("ghjk")

    assert agg.get_used_count() == 2
    assert agg.get_total_count() == 2


def test_list_aggregator():
    values = [1, 2, 3, 4]
    agg = ListAggregator()
    for val in values:
        agg.add(val)

    assert agg.get_final() == values


def test_dict_aggregator():
    values = [("first", 1), ("second", 2), ("third", 3), ("fourth", 4)]
    agg = DictAggregator()
    for key, value in values:
        agg.add(value, key=key)

    assert agg.get_final() == {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
    }
