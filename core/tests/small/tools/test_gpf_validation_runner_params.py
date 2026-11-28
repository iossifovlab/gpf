# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
from typing import Any, cast

import pytest

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.tools import gpf_validation_runner


@pytest.fixture
def runner() -> gpf_validation_runner.GenotypeBrowserRunner:
    return gpf_validation_runner.GenotypeBrowserRunner(
        {}, cast(GPFInstance, object()),
        detailed_reporting=False, skip_columns=set(),
    )


def test_parse_frequency_none_returns_none(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    assert runner._parse_frequency(cast(dict[str, Any], None)) is None


def test_parse_frequency_without_key_returns_same_object(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"genes": ["A"]}

    result = runner._parse_frequency(params)

    assert result is params
    assert result == {"genes": ["A"]}


def test_parse_frequency_ultra_rare_sets_flag_in_place(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"frequency": {"ultra_rare": True}}

    result = runner._parse_frequency(params)

    assert result is params
    assert result == {"ultra_rare": True}


@pytest.mark.parametrize("bound", ["min", "max"])
def test_parse_frequency_ultra_rare_with_a_bound_raises(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
    bound: str,
) -> None:
    params: dict[str, Any] = {"frequency": {"ultra_rare": True, bound: 1.0}}

    with pytest.raises(AssertionError):
        runner._parse_frequency(params)


def test_parse_frequency_without_bounds_raises(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"frequency": {}}

    with pytest.raises(AssertionError):
        runner._parse_frequency(params)


@pytest.mark.parametrize(
    "freq, expected_bounds",
    [
        ({"min": 0.1, "max": 5.0}, (0.1, 5.0)),
        ({"min": 0.1}, (0.1, None)),
        ({"max": 5.0}, (None, 5.0)),
    ],
)
def test_parse_frequency_sets_frequency_filter(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
    freq: dict[str, float],
    expected_bounds: tuple[float | None, float | None],
) -> None:
    params: dict[str, Any] = {"frequency": freq}

    result = runner._parse_frequency(params)

    assert result is params
    assert result == {
        "frequency_filter": [("af_allele_freq", expected_bounds)]}


def test_parse_frequency_false_ultra_rare_uses_the_bounds(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {
        "frequency": {"ultra_rare": False, "min": 0.1}}

    result = runner._parse_frequency(params)

    assert result == {
        "frequency_filter": [("af_allele_freq", (0.1, None))]}


def test_parse_genomic_scores_none_returns_none(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    assert runner._parse_genomic_scores(
        cast(dict[str, Any], None)) is None


def test_parse_genomic_scores_without_key_returns_same_object(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"genes": ["A"]}

    result = runner._parse_genomic_scores(params)

    assert result is params
    assert result == {"genes": ["A"]}


def test_parse_genomic_scores_score_without_name_raises(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"genomic_scores": [{"min": 1.0}]}

    with pytest.raises(AssertionError):
        runner._parse_genomic_scores(params)


def test_parse_genomic_scores_score_without_bounds_raises(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"genomic_scores": [{"score": "cadd"}]}

    with pytest.raises(AssertionError):
        runner._parse_genomic_scores(params)


def test_parse_genomic_scores_empty_list_removes_the_key(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"genomic_scores": [], "genes": ["A"]}

    result = runner._parse_genomic_scores(params)

    assert result is params
    assert result == {"genes": ["A"]}


def test_parse_genomic_scores_sets_real_attr_filter(
    runner: gpf_validation_runner.GenotypeBrowserRunner,
) -> None:
    params: dict[str, Any] = {"genomic_scores": [
        {"score": "cadd", "min": 1.0, "max": 2.0},
        {"score": "mpc", "min": 0.5},
        {"score": "phylop", "max": 3.0},
    ]}

    result = runner._parse_genomic_scores(params)

    assert result is params
    assert result == {"real_attr_filter": [
        ("cadd", (1.0, 2.0)),
        ("mpc", (0.5, None)),
        ("phylop", (None, 3.0)),
    ]}
