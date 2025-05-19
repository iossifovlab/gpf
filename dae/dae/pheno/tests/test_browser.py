# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
import pytest_mock

from dae.pheno.browser import PhenoBrowser
from dae.pheno.common import MeasureType


def test_create_browser_tables(
    mocker: pytest_mock.MockerFixture,
    tmp_path: pathlib.Path,
) -> None:
    spy = mocker.spy(PhenoBrowser, "create_browser_tables")
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    assert spy.call_count == 1

    tables = browser.connection.execute("SELECT * FROM duckdb_tables;").df()
    assert len(tables) == 5


def test_save(tmp_path: pathlib.Path) -> None:
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    measure = {
        "measure_id": "test_instrument.test_measure",
        "instrument_name": "test_instrument",
        "measure_name": "test_measure",
        "measure_type": 1,
        "description": "a test measure",
        "values_domain": "[0, 10]",
    }
    browser.save(measure)

    result = browser.connection.execute("SELECT * FROM variable_browser;").df()
    assert len(result) == 1


def test_save_already_existing(tmp_path: pathlib.Path) -> None:
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    measure = {
        "measure_id": "test_instrument.test_measure",
        "instrument_name": "test_instrument",
        "measure_name": "test_measure",
        "measure_type": 1,
        "description": "a test measure",
        "values_domain": "[0, 10]",
    }
    browser.save(measure)
    result = browser.connection.execute("SELECT * FROM variable_browser;").df()
    assert len(result) == 1
    assert result["description"][0] == "a test measure"

    measure["description"] = "overriding measure"
    browser.save(measure)
    result = browser.connection.execute("SELECT * FROM variable_browser;").df()
    assert len(result) == 1
    assert result["description"][0] == "overriding measure"


def test_save_regression(tmp_path: pathlib.Path) -> None:
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    regression = {
        "regression_id": "test_regression",
        "instrument_name": "test_instrument",
        "measure_name": "test_measure",
        "display_name": "Regression",
    }
    browser.save_regression(regression)

    result = browser.connection.execute("SELECT * FROM regression;").df()
    assert len(result) == 1


def test_save_regression_already_existing(tmp_path: pathlib.Path) -> None:
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    regression = {
        "regression_id": "test_regression",
        "instrument_name": "test_instrument",
        "measure_name": "test_measure",
        "display_name": "Regression",
    }
    browser.save_regression(regression)
    result = browser.connection.execute("SELECT * FROM regression;").df()
    assert len(result) == 1
    assert result["measure_name"][0] == "test_measure"

    regression["measure_name"] = "new_overriding_measure"
    browser.save_regression(regression)
    result = browser.connection.execute("SELECT * FROM regression;").df()
    assert len(result) == 1
    assert result["measure_name"][0] == "new_overriding_measure"


def test_save_regression_values(tmp_path: pathlib.Path) -> None:
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    regression_val = {
        "regression_id": "test_regression",
        "measure_id": "test_instrument.test_measure",
        "figure_regression": "blabla/fig.png",
        "figure_regression_small": "blabla/fig_small.png",
        "pvalue_regression_male": 0.1,
        "pvalue_regression_female": 0.2,
    }
    browser.save_regression_values(regression_val)
    result = browser.connection.execute("SELECT * FROM regression_values;").df()
    assert len(result) == 1


def test_save_regression_values_already_existing(
    tmp_path: pathlib.Path,
) -> None:
    db_path = str(tmp_path / "browser.db")
    browser = PhenoBrowser(db_path, read_only=False)
    regression_val = {
        "regression_id": "test_regression",
        "measure_id": "test_instrument.test_measure",
        "figure_regression": "blabla/fig.png",
        "figure_regression_small": "blabla/fig_small.png",
        "pvalue_regression_male": 0.1,
        "pvalue_regression_female": 0.2,
    }
    browser.save_regression_values(regression_val)
    result = browser.connection.execute("SELECT * FROM regression_values;").df()
    assert len(result) == 1
    assert result["pvalue_regression_male"][0] == 0.1

    regression_val["pvalue_regression_male"] = 123.456
    browser.save_regression_values(regression_val)
    result = browser.connection.execute("SELECT * FROM regression_values;").df()
    assert len(result) == 1
    assert result["pvalue_regression_male"][0] == 123.456


@pytest.mark.parametrize(
    ("instrument_name,keyword,page,expected"),
    [
        (None, None, None, {"i1.age", "i1.iq",
                            "i1.m1", "i1.m2", "i1.m3",
                            "i1.m4", "i1.m5", "i1.m6",
                            "i1.m7", "i1.m8", "i1.m9", "i1.m10",
                            "i2.m1",
                            "i3.m1",
                            "i4.m1"}),
        ("i2", None, None, {"i2.m1"}),
        (None, "i2", None, {"i2.m1"}),
        (None, "m1", None, {"i1.m1", "i1.m10",
                            "i2.m1",
                            "i3.m1",
                            "i4.m1"}),
        # the keyword here is found in the descriptions of these measures
        (None, "Measure number", None, {"i1.m1", "i1.m2", "i1.m9"}),
        # page size is 1001 and there's only 17 measures; result should be empty
        (None, None, 2, set()),
    ],
)
def test_search_measures(
    fake_pheno_browser: PhenoBrowser,
    instrument_name: str | None,
    keyword: str | None,
    page: int | None,
    expected: set[str],
) -> None:
    result = fake_pheno_browser.search_measures(
        instrument_name=instrument_name,
        keyword=keyword,
        page=page,
    )
    assert {measure["measure_id"] for measure in result} == expected


@pytest.mark.parametrize(
    ("sort_by,order_by,expected"),
    [
        ("instrument", None, ["i1.age", "i1.iq",
                              "i1.m1", "i1.m10", "i1.m2", "i1.m3",
                              "i1.m4", "i1.m5", "i1.m6",
                              "i1.m7", "i1.m8", "i1.m9",
                              "i2.m1",
                              "i3.m1",
                              "i4.m1"]),
        ("instrument", "asc", ["i1.age", "i1.iq",
                               "i1.m1", "i1.m10", "i1.m2", "i1.m3",
                               "i1.m4", "i1.m5", "i1.m6",
                               "i1.m7", "i1.m8", "i1.m9",
                               "i2.m1",
                               "i3.m1",
                               "i4.m1"]),
        ("instrument", "desc", list(reversed(
                               ["i1.age", "i1.iq",
                                "i1.m1", "i1.m10", "i1.m2", "i1.m3",
                                "i1.m4", "i1.m5", "i1.m6",
                                "i1.m7", "i1.m8", "i1.m9",
                                "i2.m1",
                                "i3.m1",
                                "i4.m1"]))),
        ("measure", None, ["age", "iq",
                           "m1", "m1", "m1", "m1",
                           "m10",
                           "m2",
                           "m3",
                           "m4", "m5", "m6",
                           "m7", "m8", "m9"]),
        # nine continuous, two ordinal, one categorical and five raw measures
        ("measure_type", None, [*[MeasureType.continuous] * 7,
                                *[MeasureType.ordinal] * 4,
                                *[MeasureType.categorical] * 1,
                                *[MeasureType.raw] * 3]),
        # three measures with descriptions, fourteen without
        ("description", None, [*[''] * 12,  # noqa Q000
                               "Measure number nine",
                               "Measure number one",
                               "Measure number two"]),
    ],
)
def test_search_measures_order_and_sort(
    fake_pheno_browser: PhenoBrowser,
    sort_by: str,
    order_by: str | None,
    expected: list[str],
) -> None:
    result = fake_pheno_browser.search_measures(
        sort_by=sort_by, order_by=order_by,
    )

    col_map = {
        "instrument": "measure_id",
        "measure": "measure_name",
        "measure_type": "measure_type",
        "description": "description",
    }
    col = col_map[sort_by]

    assert [measure[col] for measure in result] == expected


@pytest.mark.parametrize(
    ("instrument_name,keyword,page,expected"),
    [
        (None, None, None, 15),
        ("i2", None, None, 1),
        (None, "i2", None, 1),
        (None, "m1", None, 5),
        # the keyword here is found in the descriptions of these measures
        (None, "Measure number", None, 3),
        # page size is 1001 and there's only 17 measures; result should be empty
        (None, None, 2, 0),
    ],
)
def test_count_measures(
    fake_pheno_browser: PhenoBrowser,
    instrument_name: str | None,
    keyword: str | None,
    page: int | None,
    expected: int,
) -> None:
    result = fake_pheno_browser.count_measures(
        instrument_name=instrument_name,
        keyword=keyword,
        page=page,
    )
    assert result == expected


def test_regression_ids(fake_pheno_browser: PhenoBrowser) -> None:
    assert fake_pheno_browser.regression_ids == ["age", "nviq"]


def test_regression_display_names(fake_pheno_browser: PhenoBrowser) -> None:
    assert fake_pheno_browser.regression_display_names_with_ids == {
        "age": {
            "display_name": "age",
            "instrument_name": "i1",
            "measure_name": "age",
        },
        "nviq": {
            "display_name": "nonverbal iq",
            "instrument_name": "i1",
            "measure_name": "iq",
        },
    }


def test_regression_display_names_with_ids(
    fake_pheno_browser: PhenoBrowser,
) -> None:
    assert fake_pheno_browser.regression_display_names_with_ids == {
        "age": {
            "display_name": "age",
            "instrument_name": "i1",
            "measure_name": "age",
        },
        "nviq": {
            "display_name": "nonverbal iq",
            "instrument_name": "i1",
            "measure_name": "iq",
        },
    }


def test_has_measure_descriptions(fake_pheno_browser: PhenoBrowser) -> None:
    assert fake_pheno_browser.has_measure_descriptions is True
