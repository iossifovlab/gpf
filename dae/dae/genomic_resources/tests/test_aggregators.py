import numpy
from dae.genomic_resources.aggregators import (
    ConcatAggregator, MinAggregator,
    MaxAggregator, MeanAggregator,
    ModeAggregator, MedianAggregator,
    JoinAggregator
)


def test_concat_aggregator():
    values = ["a", "b", "c", "d"]
    agg = ConcatAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == "abcd"


def test_min_aggregator():
    values = [5, 6, 1, 2, 7]
    agg = MinAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == 1


def test_min_aggregator_string():
    values = ["asdf", "ghjk", "zab", "zob"]
    agg = MinAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == "asdf"


def test_max_aggregator():
    values = [5, 6, 1, 2, 7]
    agg = MaxAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == 7


def test_max_aggregator_string():
    values = ["asdf", "ghjk", "zab", "zob"]
    agg = MaxAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == "zob"


def test_mean_aggregator():
    values = [1, 2, 3, 4]
    agg = MeanAggregator()
    for v in values:
        agg.add(v)

    assert numpy.isclose(agg.get_final(), 2.5)


def test_median_aggregator_even():
    values = [2, 3, 4, 1]
    agg = MedianAggregator()
    for v in values:
        agg.add(v)

    assert numpy.isclose(agg.get_final(), 2.5)


def test_median_aggregator_odd():
    values = [2, 3, 4, 1, 5]
    agg = MedianAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == 3


def test_median_aggregator_string_even():
    values = ["a", "c", "b", "d"]
    agg = MedianAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == "bc"


def test_median_aggregator_string_odd():
    values = ["a", "c", "b", "d", "f"]
    agg = MedianAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == "c"


def test_mode_aggregator():
    values = [1, 2, 3, 1, 5, 6, 6, 1]
    agg = ModeAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == 1


def test_mode_aggregator_multimode():
    values = [6, 2, 3, 6, 5, 1, 1, 6, 1, 4, 4, 4]
    agg = ModeAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_final() == 1


def test_join_aggregator():
    values = [1, 2, 3, 4, 5]
    agg = JoinAggregator(", ")
    for v in values:
        agg.add(v)

    assert agg.get_final() == "1, 2, 3, 4, 5"


def test_aggregator_used_counts():
    values = [1, 2, 3, None, None, 4, 5]
    agg = MinAggregator()
    for v in values:
        agg.add(v)

    assert agg.get_used_count() == 5
    assert agg.get_total_count() == 7
    agg.clear()
    assert agg.get_used_count() == 0
    assert agg.get_total_count() == 0

    agg.add("asdf")
    agg.add("ghjk")

    assert agg.get_used_count() == 2
    assert agg.get_total_count() == 2
