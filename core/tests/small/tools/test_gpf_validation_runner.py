# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
from typing import Any, cast

import pandas as pd
import pytest

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.tools.gpf_validation_runner import GenotypeBrowserRunner, main

KEY_COLUMNS = ["chromosome", "position", "reference", "alternative",
               "family_id"]


def _frame(**columns: list[Any]) -> pd.DataFrame:
    """Build a two-row variants frame with extra columns."""
    data: dict[str, list[Any]] = {
        "chromosome": ["1", "1"],
        "position": [10, 20],
        "reference": ["A", "C"],
        "alternative": ["G", "T"],
        "family_id": ["f1", "f2"],
    }
    data.update(columns)
    return pd.DataFrame(data)


@pytest.fixture
def runner() -> GenotypeBrowserRunner:
    return GenotypeBrowserRunner(
        {}, cast(GPFInstance, object()),
        detailed_reporting=False, skip_columns=set(),
    )


def test_variants_diff_both_empty_is_none(
    runner: GenotypeBrowserRunner,
) -> None:
    empty = pd.DataFrame({c: [] for c in KEY_COLUMNS})

    assert runner._variants_diff(empty, empty.copy()) is None


def test_variants_diff_equal_frames_is_none(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(score=[1.0, 2.0], effect=["a", "b"])

    assert runner._variants_diff(variants, variants.copy()) is None


def test_variants_diff_float_within_1e_4_is_none(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(score=[1.0, 2.0])
    expected = _frame(score=[1.00001, 2.0])

    assert runner._variants_diff(variants, expected) is None


def test_variants_diff_reports_a_float_gap_just_above_1e_4(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(score=[1.0, 2.0])
    expected = _frame(score=[1.0002, 2.0])

    result = runner._variants_diff(variants, expected)

    assert result is not None
    assert result.splitlines()[0] == "Columns with differences: ['score']"


def test_variants_diff_reports_a_float_column_above_1e_4(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(score=[1.0, 2.0])
    expected = _frame(score=[1.5, 2.0])

    result = runner._variants_diff(variants, expected)

    assert result is not None
    lines = result.splitlines()
    assert lines[0] == "Columns with differences: ['score']"
    assert lines[1] == "Column score differences:"
    assert lines[2].split() == [
        "chromosome", "position", "reference", "alternative",
        "variants_score", "expected_score"]
    assert lines[3].split() == ["0", "1", "10", "A", "G", "1.0", "1.5"]
    assert len(lines) == 4


def test_variants_diff_reports_a_string_column(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(effect=["a", "b"])
    expected = _frame(effect=["a", "c"])

    result = runner._variants_diff(variants, expected)

    assert result is not None
    lines = result.splitlines()
    assert lines[0] == "Columns with differences: ['effect']"
    assert lines[1] == "Column effect differences:"
    assert lines[3].split() == ["1", "1", "20", "C", "T", "b", "c"]
    assert len(lines) == 4


def test_variants_diff_ignores_a_falsy_different_value(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(count=[0, 2])
    expected = _frame(count=[1, 2])

    assert runner._variants_diff(variants, expected) is None


def test_variants_diff_reports_a_header_mismatch(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(a=[1, 2])
    expected = _frame(b=[1, 2])

    result = runner._variants_diff(variants, expected)

    assert result is not None
    assert result.splitlines()[-1] == (
        "Header mismatch: "
        "['a', 'alternative', 'chromosome', 'family_id', 'position', "
        "'reference'] vs "
        "['alternative', 'b', 'chromosome', 'family_id', 'position', "
        "'reference']")


def test_variants_diff_reports_a_length_mismatch(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame()
    expected = _frame().iloc[:1]

    result = runner._variants_diff(variants, expected)

    assert result == (
        "expected 1 variants; got 2\n"
        "Length mismatch: 2 vs expected 1\n")


def test_variants_diff_length_check_wins_over_header_check(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(a=[1, 2])
    expected = _frame(b=[1, 2]).iloc[:1]

    result = runner._variants_diff(variants, expected)

    assert result is not None
    assert result.splitlines()[-1] == "Length mismatch: 2 vs expected 1"


def test_variants_diff_rows_in_other_order_log_and_return_none(
    runner: GenotypeBrowserRunner,
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected = _frame(effect=["a", "b"])
    variants = _frame(effect=["a", "x"]).iloc[::-1].reset_index(drop=True)

    result = runner._variants_diff(variants, expected)

    assert result is None
    assert "unexpected exception whild running tests" in caplog.text
    assert "ValueError" in caplog.text


def test_error_reporter2_float_tolerance_is_1e_6(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(effect=["a", "x"], score=[1.0, 2.0])
    expected = _frame(effect=["a", "b"], score=[1.0, 2.00001])

    result = runner._variants_diff(variants, expected)

    assert result is not None
    lines = result.splitlines()
    assert lines[0] == "Columns with differences: ['effect']"
    assert lines[1] == "Column effect differences:"
    assert lines[3].split() == ["1", "1", "20", "C", "T", "x", "b"]
    assert lines[4] == "Column score differences:"
    assert lines[6].split() == ["1", "1", "20", "C", "T", "2.0", "2.00001"]
    assert len(lines) == 7


def test_error_reporter2_prints_the_assertion_first(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(effect=["a", "x"])
    expected = _frame(effect=["a", "b"])

    result = runner._error_reporter2(
        AssertionError("custom message"), variants, expected)

    assert result.splitlines()[0] == "custom message"
    assert result.splitlines()[1] == "Column effect differences:"


def test_error_reporter2_no_differing_column_prints_only_the_assertion(
    runner: GenotypeBrowserRunner,
) -> None:
    variants = _frame(count=[0, 2], score=[1.0, 2.0])
    expected = _frame(count=[1, 2], score=[1.0, 2.0])

    result = runner._error_reporter2(
        AssertionError("custom message"), variants, expected)

    assert result == "custom message\n"


def test_main_help_exits_with_code_0() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0


def test_main_unknown_option_exits_with_code_2() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--no-such-option"])

    assert exc_info.value.code == 2
