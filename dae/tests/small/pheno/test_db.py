# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from pathlib import Path
from typing import Any

import pytest
from dae.pheno.browser import PhenoBrowser
from dae.pheno.common import MeasureType
from dae.pheno.db import safe_db_name
from dae.pheno.registry import PhenoRegistry


def test_browser_save(tmp_path: str) -> None:
    dbfile = Path(tmp_path) / "browser.db"
    browser = PhenoBrowser(str(dbfile), read_only=False)
    assert browser is not None

    v = {
        "measure_id": "test.measure",
        "instrument_name": "test",
        "measure_name": "measure",
        "measure_type": MeasureType.other.value,
        "description": "desc",
    }

    browser.save(v)

    res = next(browser.search_measures(keyword="test.measure"))
    assert res is not None

    assert res["measure_id"] == "test.measure"
    assert res["instrument_name"] == "test"
    assert res["measure_name"] == "measure"
    assert res["figure_distribution"] is None


def test_browser_update(tmp_path: str) -> None:
    dbfile = Path(tmp_path) / "browser.db"
    browser = PhenoBrowser(str(dbfile), read_only=False)
    assert browser is not None

    v: dict[str, Any] = {
        "measure_id": "test.measure",
        "instrument_name": "test",
        "measure_name": "measure",
        "measure_type": MeasureType.other.value,
        "description": "desc",
    }
    browser.save(v)
    v["measure_id"] = "test.measure"
    v["figure_distribution"] = "test_figure.png"
    browser.save(v)

    res = next(browser.search_measures(keyword="test.measure"))
    assert res is not None
    assert res["measure_id"] == "test.measure"
    assert res["instrument_name"] == "test"
    assert res["measure_name"] == "measure"
    assert res["figure_distribution"] == "test_figure.png"


def test_browser_has_measure_descriptions(tmp_path: str) -> None:
    dbfile = Path(tmp_path) / "browser.db"
    browser = PhenoBrowser(str(dbfile), read_only=False)
    assert browser is not None

    for i in range(3):
        v = {
            "measure_id": f"test.measure{i}",
            "instrument_name": "test",
            "measure_name": f"measure{i}",
            "measure_type": MeasureType.other.value,
            "description": None,
        }
        browser.save(v)
    assert not browser.has_measure_descriptions

    v = {
        "measure_id": "test.measure4",
        "instrument_name": "test",
        "measure_name": "measure4",
        "measure_type": MeasureType.other.value,
        "description": "a description",
    }
    browser.save(v)
    assert browser.has_measure_descriptions


def test_search_measures_get_all(
    fake_phenotype_data_browser_dbfile: str,
) -> None:
    browser = PhenoBrowser(
        fake_phenotype_data_browser_dbfile,
        read_only=True,
    )
    assert browser is not None
    measures = list(browser.search_measures())
    print(measures)
    assert len(measures) == 15
    assert [measure.get("instrument_name") for measure in measures] == [
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i1",
        "i2",
        "i3",
        "i4",
    ]


def test_search_measures_get_by_instrument(
    fake_phenotype_data_browser_dbfile: str,
) -> None:
    browser = PhenoBrowser(
        fake_phenotype_data_browser_dbfile,
        read_only=True,
    )
    assert browser is not None
    measures = list(browser.search_measures("i1", None))
    assert len(measures) == 12
    for row in measures:
        assert row["instrument_name"] == "i1"

    measures = list(browser.search_measures("i2", None))
    assert len(measures) == 1
    for row in measures:
        assert row["instrument_name"] == "i2"


def test_search_measures_by_keyword_in_measure_id(
    fake_phenotype_data_browser_dbfile: str,
) -> None:
    browser = PhenoBrowser(
        fake_phenotype_data_browser_dbfile,
        read_only=True,
    )
    assert browser is not None
    measures = list(browser.search_measures(None, "i1.m2"))
    assert len(measures) == 1
    assert measures[0]["measure_name"] == "m2"
    assert measures[0]["instrument_name"] == "i1"


def test_search_measures_by_keyword_in_measure_name(
    fake_phenotype_data_browser_dbfile: str,
) -> None:
    browser = PhenoBrowser(
        fake_phenotype_data_browser_dbfile,
        read_only=True,
    )
    assert browser is not None
    measures = list(browser.search_measures(None, "m2"))
    assert len(measures) == 1
    assert measures[0]["measure_name"] == "m2"
    assert measures[0]["instrument_name"] == "i1"


def test_search_measures_by_keyword_in_instrument_name(
    fake_phenotype_data_browser_dbfile: str,
) -> None:
    browser = PhenoBrowser(
        fake_phenotype_data_browser_dbfile,
        read_only=True,
    )
    assert browser is not None

    measures = list(browser.search_measures(None, "i"))
    assert len(measures) == 15

    measures = list(browser.search_measures(None, "i1"))
    assert len(measures) == 12
    for row in measures:
        assert row["instrument_name"] == "i1"


def test_db_search_character_escaping(
    fake_browserdb_file_copy: str,
) -> None:
    browser = PhenoBrowser(
        fake_browserdb_file_copy,
        read_only=False,
    )
    assert browser is not None

    val1: dict[str, Any] = {
        "measure_id": "test_one.measure1",
        "instrument_name": "test_one",
        "measure_name": "measure1",
        "measure_type": MeasureType.other.value,
        "description": "desc",
    }

    val2: dict[str, Any] = {
        "measure_id": "test%two.measure2",
        "instrument_name": "test%two",
        "measure_name": "measure2",
        "measure_type": MeasureType.other.value,
        "description": "desc",
    }

    browser.save(val1)
    browser.save(val2)

    res = list(browser.search_measures(keyword="test_one"))
    assert res is not None
    assert len(res) == 1
    assert res[0]["measure_id"] == "test_one.measure1"
    assert res[0]["instrument_name"] == "test_one"
    assert res[0]["measure_name"] == "measure1"

    res = list(browser.search_measures(keyword="test%two"))
    assert res is not None
    assert len(res) == 1
    assert res[0]["measure_id"] == "test%two.measure2"
    assert res[0]["instrument_name"] == "test%two"
    assert res[0]["measure_name"] == "measure2"


def test_get_regression_names(fake_browserdb_file_copy: str) -> None:
    browser = PhenoBrowser(
        fake_browserdb_file_copy,
        read_only=False,
    )
    assert browser is not None

    reg = {}
    reg["regression_id"] = "test_regression"
    reg["instrument_name"] = "test_instrument"
    reg["measure_name"] = "test_measure"
    reg["display_name"] = "a test regression with a display name"
    browser.save_regression(reg)

    reg["regression_id"] = "test_regression2"
    reg["instrument_name"] = "test_instrument"
    reg["measure_name"] = "test_measure2"
    reg["display_name"] = "a second test regression with a display name"
    browser.save_regression(reg)

    reg_names = browser.regression_display_names
    assert reg_names == {
        "test_regression": "a test regression with a display name",
        "test_regression2": "a second test regression with a display name",
        "age": "age",
        "nviq": "nonverbal iq",
    }


def test_regression_ids(fake_browserdb_file_copy: str) -> None:
    browser = PhenoBrowser(
        fake_browserdb_file_copy,
        read_only=False,
    )
    assert browser is not None

    reg = {}

    reg["regression_id"] = "test_regression_1"
    reg["instrument_name"] = "test"
    reg["measure_name"] = "regressor1"
    browser.save_regression(reg)

    reg["regression_id"] = "test_regression_2"
    reg["instrument_name"] = "test"
    reg["measure_name"] = "regressor2"
    browser.save_regression(reg)

    reg_ids = browser.regression_ids
    for reg_id in ["test_regression_1", "test_regression_2"]:
        assert reg_id in reg_ids


def test_pheno_db_disabled(fake_pheno_db: PhenoRegistry) -> None:
    assert not fake_pheno_db.has_phenotype_data("fake_disabled")


@pytest.mark.parametrize("iinput,expected", [
    ("abc", "abc"),
    ("ABC", "abc"),
    ("abc1", "abc1"),
    ("1abc", "_1abc"),
    (" 1abc", "_1abc"),
    ("a b c", "a_b_c"),
    ("a.b.c", "a_b_c"),
    ("a-b-c", "a_b_c"),
    ("a/b/c", "a_b_c"),
    ("a.b.c a/b/c a-b-c", "a_b_c_a_b_c_a_b_c"),
])
def test_safe_db_name(iinput: str, expected: str) -> None:
    assert safe_db_name(iinput) == expected


def test_safe_db_name_invalid() -> None:
    with pytest.raises(ValueError, match="empty"):
        assert safe_db_name("")
