# pylint: disable=C0114,C0116
from typing import Any

import pytest

from gpf.pheno_tool.pheno_tool_adapter import PhenoToolAdapter


def group(count: Any, mean: Any, deviation: Any = 0) -> dict[str, Any]:
    return {"count": count, "mean": mean, "deviation": deviation}


def sex_result(
    positive: dict[str, Any],
    negative: dict[str, Any],
    p_value: Any = 0.5,
) -> dict[str, Any]:
    return {"positive": positive, "negative": negative, "pValue": p_value}


def full() -> dict[str, Any]:
    return sex_result(group(3, 1.5, 0.2), group(4, 2.5, 0.3))


def test_empty_results_list_is_a_noop() -> None:
    results: list[dict[str, Any]] = []

    PhenoToolAdapter.align_na_results(results)

    assert not results


def test_nonzero_counts_change_nothing() -> None:
    results = [{"femaleResults": full(), "maleResults": full()}]

    PhenoToolAdapter.align_na_results(results)

    assert results == [{"femaleResults": full(), "maleResults": full()}]


def test_empty_positive_group_takes_the_negative_mean() -> None:
    female = sex_result(group(0, 0), group(4, 2.5, 0.3), "NA")
    results = [{"femaleResults": female, "maleResults": full()}]

    PhenoToolAdapter.align_na_results(results)

    assert female["positive"] == group(0, 2.5)
    assert female["negative"] == group(4, 2.5, 0.3)
    assert results[0]["maleResults"] == full()


def test_empty_negative_group_takes_the_positive_mean() -> None:
    male = sex_result(group(3, 1.5, 0.2), group(0, 0), "NA")
    results = [{"femaleResults": full(), "maleResults": male}]

    PhenoToolAdapter.align_na_results(results)

    assert male["negative"] == group(0, 1.5)
    assert male["positive"] == group(3, 1.5, 0.2)
    assert results[0]["femaleResults"] == full()


def test_negative_check_reads_the_positive_mean_written_before_it() -> None:
    # Both groups are empty. The positive check copies the negative mean
    # (False) into the positive mean. The negative check then copies that
    # False back, not the original positive mean (the int 0).
    female = sex_result(group(0, 0), group(0, mean=False), "NA")
    results = [{"femaleResults": female, "maleResults": full()}]

    PhenoToolAdapter.align_na_results(results)

    assert female["positive"]["mean"] is False
    assert female["negative"]["mean"] is False


def test_each_result_of_the_list_is_aligned() -> None:
    first = sex_result(group(0, 0), group(4, 2.5), "NA")
    second = sex_result(group(5, 7.0), group(0, 0), "NA")
    results = [
        {"femaleResults": full(), "maleResults": first},
        {"femaleResults": second, "maleResults": full()},
    ]

    PhenoToolAdapter.align_na_results(results)

    assert first["positive"]["mean"] == 2.5
    assert second["negative"]["mean"] == 7.0


def test_female_results_are_aligned_before_male_results() -> None:
    female = sex_result(group(0, 0), group(4, 2.5), "NA")
    male = sex_result(group(0, 1.0), group(4, 2.5), "NA")
    results = [{"femaleResults": female, "maleResults": male}]

    with pytest.raises(AssertionError):
        PhenoToolAdapter.align_na_results(results)

    assert female["positive"]["mean"] == 2.5
    assert male["positive"]["mean"] == 1.0


@pytest.mark.parametrize(
    "positive,p_value",
    [
        pytest.param(group(0, 1.0), "NA", id="mean-not-zero"),
        pytest.param(group(0, 0, 0.1), "NA", id="deviation-not-zero"),
        pytest.param(group(0, 0), 0.5, id="p-value-not-na"),
    ],
)
def test_empty_positive_group_with_bad_values_raises(
    positive: dict[str, Any], p_value: Any,
) -> None:
    female = sex_result(positive, group(4, 2.5), p_value)
    results = [{"femaleResults": female, "maleResults": full()}]

    with pytest.raises(AssertionError):
        PhenoToolAdapter.align_na_results(results)

    assert female["positive"]["mean"] == positive["mean"]


@pytest.mark.parametrize(
    "negative,p_value",
    [
        pytest.param(group(0, 1.0), "NA", id="mean-not-zero"),
        pytest.param(group(0, 0, 0.1), "NA", id="deviation-not-zero"),
        pytest.param(group(0, 0), 0.5, id="p-value-not-na"),
    ],
)
def test_empty_negative_group_with_bad_values_raises(
    negative: dict[str, Any], p_value: Any,
) -> None:
    male = sex_result(group(3, 1.5), negative, p_value)
    results = [{"femaleResults": full(), "maleResults": male}]

    with pytest.raises(AssertionError):
        PhenoToolAdapter.align_na_results(results)

    assert male["negative"]["mean"] == negative["mean"]


def test_float_and_false_zeros_pass_the_checks() -> None:
    female = sex_result(group(0.0, 0.0, 0.0), group(4, 2.5), "NA")
    male = sex_result(
        group(3, 1.5), group(count=False, mean=False, deviation=False), "NA",
    )
    results = [{"femaleResults": female, "maleResults": male}]

    PhenoToolAdapter.align_na_results(results)

    assert female["positive"]["mean"] == 2.5
    assert male["negative"]["mean"] == 1.5


@pytest.mark.parametrize("missing", ["femaleResults", "maleResults"])
def test_result_without_a_sex_key_raises_key_error(missing: str) -> None:
    result = {"femaleResults": full(), "maleResults": full()}
    del result[missing]

    with pytest.raises(KeyError, match=missing):
        PhenoToolAdapter.align_na_results([result])
