# pylint: disable=W0621,C0114,C0116,W0212,W0613
from inspect import isgenerator
import pytest

from dae.utils.dae_utils import split_iterable


def test_splits_empty_iterable():
    gen = split_iterable(iter(""), 5)

    assert isgenerator(gen)

    for val in gen:
        print(val)
        pytest.fail("should be an empty generator")


def test_splists_perfectly():
    gen = split_iterable("asddsa", 3)

    i = 0
    for val in gen:
        assert len(val) == 3
        i += 1

    assert i == 2


def test_splits_left_to_right():
    gen = split_iterable("asddsa", 3)

    val1 = next(gen)
    val2 = next(gen)

    assert val1 == ["a", "s", "d"]
    assert val2 == ["d", "s", "a"]


def test_imperfectly_yields_all_parts():
    gen = split_iterable("asd", 2)

    val1 = next(gen)
    val2 = next(gen)

    assert len(val1) == 2
    assert len(val2) == 1


def test_consumes_given_iterable():
    iterator = iter("asddsa")
    gen = split_iterable(iterator, 3)

    gen = list(gen)  # consumes result

    for _ in iterator:
        pytest.fail("should have been consumed")
