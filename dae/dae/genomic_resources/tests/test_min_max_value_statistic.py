import pytest

from dae.genomic_resources.statistics.base_statistic import Statistic
from dae.genomic_resources.statistics.min_max import (
    MinMaxValue,
    MinMaxValueStatisticMixin,
)


def test_min_max_value_add_value() -> None:
    """Test adding value to min max value statistic"""
    min_max_value = MinMaxValue("test_score", 5, 10)

    assert min_max_value.min == 5
    assert min_max_value.max == 10

    min_max_value.add_value(None)
    assert min_max_value.min == 5
    assert min_max_value.max == 10

    min_max_value.add_value(3)
    assert min_max_value.min == 3
    assert min_max_value.max == 10

    min_max_value.add_value(12)
    assert min_max_value.min == 3
    assert min_max_value.max == 12


def test_min_max_value_merge_with_min_max_statistics() -> None:
    """Test merging min max value statistic with another statistic"""
    min_max_value = MinMaxValue("test_score", 5, 10)
    other_min_max_value = MinMaxValue("test_score", 7, 15, 2)
    min_max_value.merge(other_min_max_value)
    assert min_max_value.min == 5
    assert min_max_value.max == 15
    assert min_max_value.count == 2


def test_min_max_value_merge_with_different_statistic_type() -> None:
    """Test merging min max value statistic with basic statistic"""
    min_max_value = MinMaxValue("test_score", 5, 10)
    other_statistic = Statistic("stat_id", "desc")
    with pytest.raises(TypeError) as error_msg:
        min_max_value.merge(other_statistic)
    assert "unexpected type" in str(error_msg.value)


def test_min_max_value_merge_with_different_scores() -> None:
    """Test merging min max value statistic with another with different score"""
    min_max_value = MinMaxValue("test_score", 5, 10)
    other_min_max_value = MinMaxValue("other_test_score", 7, 15)
    with pytest.raises(ValueError) as error_msg:  # noqa: PT011
        min_max_value.merge(other_min_max_value)
    assert "different scores" in str(error_msg.value)


def test_min_max_value_add_count() -> None:
    """Test min max value statistic count"""
    min_max_value = MinMaxValue("test_score", 5, 10)

    assert min_max_value.count == 0
    min_max_value.add_count(9)
    assert min_max_value.count == 9
    min_max_value.add_count(11)
    assert min_max_value.count == 20


def test_min_max_value_serialize() -> None:
    """Test min max value serialize"""
    min_max_value = MinMaxValue("test_score", 5, 10)

    min_max_serialized = min_max_value.serialize()
    assert min_max_serialized == "max: 10\nmin: 5\nscore_id: test_score\n"

    min_max_value.add_count(7)
    min_max_serialized = min_max_value.serialize()
    assert min_max_serialized == (
        "count: 7\nmax: 10\nmin: 5\nscore_id: test_score\n"
    )


def test_min_max_value_deserialize() -> None:
    """Test min max value deserialize"""
    min_max_value = MinMaxValue.deserialize(
        "max: 10\nmin: 5\nscore_id: test_score\n",
    )

    assert min_max_value.score_id == "test_score"
    assert min_max_value.min == 5
    assert min_max_value.max == 10

    min_max_value = MinMaxValue.deserialize(
        "count: 7\nmax: 10\nmin: 5\nscore_id: test_score\n",
    )

    assert min_max_value.score_id == "test_score"
    assert min_max_value.min == 5
    assert min_max_value.max == 10
    assert min_max_value.count == 7


def test_min_max_value_statistic_mixin() -> None:
    """Test min max value deserialize"""
    min_max_file = MinMaxValueStatisticMixin.get_min_max_file("test_score")
    assert min_max_file == "min_max_test_score.yaml"
