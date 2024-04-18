# pylint: disable=W0621,C0114,C0116,W0212,W0613,W0104
import pytest

from dae.utils.statistics import StatsCollection


@pytest.fixture()
def stats_fixture() -> StatsCollection:
    stats = StatsCollection()
    assert stats is not None

    stats[("a", )] = 1
    stats[("b", "1")] = 1
    stats[("b", "2")] = 2
    return stats


def test_stats_simple(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture

    assert stats.get(("a", )) == 1
    assert stats.get(("b", "1")) == 1
    assert stats.get(("b", "2")) == 2


def test_stats_get(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture

    assert stats[("b", "1")] == 1
    assert stats.get(("b", "3")) == 0

    assert stats.get(("c",)) == 0


def test_stats_len(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture
    assert len(stats) == 3


def test_stats_items(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture
    result = list(stats.items())
    assert result == [
        (("a", ), 1),
        (("b", "1"), 1),
        (("b", "2"), 2),
    ]


def test_stats_values(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture
    assert list(stats.values()) == [
        1,
        1,
        2,
    ]


def test_stats_keys(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture
    assert list(stats.keys()) == [
        ("a", ),
        ("b", "1"),
        ("b", "2"),
    ]


def test_stats_get_multi(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture

    assert stats[("b",)] == {
        ("b", "1"): 1,
        ("b", "2"): 2,
    }


def test_stats_get_multi2(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture
    stats[("a", "3")] = 3
    stats[("a", "4")] = 4

    assert stats[("a",)] == {
        ("a",): 1,
        ("a", "3"): 3,
        ("a", "4"): 4,
    }


def test_stats_default_0(stats_fixture: StatsCollection) -> None:
    stats = stats_fixture

    stats.inc(("tttt",))
    assert stats[("tttt",)] == 1

    stats.inc(("tttt",))
    assert stats[("tttt",)] == 2

    stats.inc(("tttt", "tttt"))
    assert stats[("tttt", "tttt")] == 1
