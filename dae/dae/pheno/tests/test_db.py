# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from typing import Any

from dae.pheno.common import MeasureType
from dae.pheno.db import PhenoDb
from dae.pheno.registry import PhenoRegistry


def test_db_save(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
        read_only=False,
    )
    assert db is not None

    v = {
        "measure_id": "test.measure",
        "instrument_name": "test",
        "measure_name": "measure",
        "measure_type": MeasureType.other.value,
        "description": "desc",
    }

    db.save(v)  # type: ignore

    res = db.get_browser_measure("test.measure")
    assert res is not None

    assert res["measure_id"] == "test.measure"
    assert res["instrument_name"] == "test"
    assert res["measure_name"] == "measure"
    assert res["figure_distribution"] is None


def test_db_update(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
        read_only=False,
    )
    assert db is not None

    v: dict[str, Any] = {
        "measure_id": "test.measure",
        "instrument_name": "test",
        "measure_name": "measure",
        "measure_type": MeasureType.other.value,
        "description": "desc",
    }
    print(v)
    db.save(v)
    print(v)
    v["measure_id"] = "test.measure"
    v["figure_distribution"] = "test_figure.png"
    db.save(v)

    res = db.get_browser_measure("test.measure")
    assert res is not None
    assert res["measure_id"] == "test.measure"
    assert res["instrument_name"] == "test"
    assert res["measure_name"] == "measure"
    assert res["figure_distribution"] == "test_figure.png"


def test_has_descriptions(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
        read_only=False,
    )
    assert db is not None

    for i in range(3):
        v = {
            "measure_id": f"test.measure{i}",
            "instrument_name": "test",
            "measure_name": f"measure{i}",
            "measure_type": MeasureType.other.value,
            "description": None,
        }
        db.save(v)
    assert not db.has_descriptions

    v = {
        "measure_id": "test.measure4",
        "instrument_name": "test",
        "measure_name": "measure4",
        "measure_type": MeasureType.other.value,
        "description": "a description",
    }
    db.save(v)
    assert db.has_descriptions


def test_search_measures_get_all(
    fake_phenotype_data_dbfile: str, fake_phenotype_data_browser_dbfile: str,
) -> None:
    db = PhenoDb(
        fake_phenotype_data_dbfile,
    )
    assert db is not None
    measures = list(db.search_measures())
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
        "i2",
        "i2",
    ]


def test_search_measures_get_by_instrument(
    fake_phenotype_data_dbfile: str, fake_phenotype_data_browser_dbfile: str,
) -> None:
    db = PhenoDb(
        fake_phenotype_data_dbfile,
    )
    assert db is not None
    measure_df = db.search_measures_df("i1", None)
    assert len(measure_df) == 12
    for _, row in measure_df.iterrows():
        assert row["instrument_name"] == "i1"

    measure_df = db.search_measures_df("i2", None)
    assert len(measure_df) == 3
    print(measure_df)
    for _, row in measure_df.iterrows():
        assert row["instrument_name"] == "i2"


def test_search_measures_by_keyword_in_description(
    fake_phenotype_data_dbfile: str, fake_phenotype_data_browser_dbfile: str,
) -> None:
    db = PhenoDb(
        fake_phenotype_data_dbfile,
    )
    assert db is not None
    measure_df = db.search_measures_df(None, "number")
    assert len(measure_df) == 3
    for _, row in measure_df.iterrows():
        assert "number" in row["description"]


def test_search_measures_by_keyword_in_measure_id(
    fake_phenotype_data_dbfile: str, fake_phenotype_data_browser_dbfile: str,
) -> None:
    db = PhenoDb(
        fake_phenotype_data_dbfile,
    )
    assert db is not None
    measure_df = db.search_measures_df(None, "i1.m2")
    assert len(measure_df) == 1
    assert measure_df.iloc[0]["measure_name"] == "m2"
    assert measure_df.iloc[0]["instrument_name"] == "i1"


def test_search_measures_by_keyword_in_measure_name(
    fake_phenotype_data_dbfile: str, fake_phenotype_data_browser_dbfile: str,
) -> None:
    db = PhenoDb(
        fake_phenotype_data_dbfile,
    )
    assert db is not None
    measure_df = db.search_measures_df(None, "m2")
    assert len(measure_df) == 2
    assert measure_df.iloc[0]["measure_name"] == "m2"
    assert measure_df.iloc[0]["instrument_name"] == "i1"
    assert measure_df.iloc[1]["measure_name"] == "m2"
    assert measure_df.iloc[1]["instrument_name"] == "i2"


def test_search_measures_by_keyword_in_instrument_name(
    fake_phenotype_data_dbfile: str, fake_phenotype_data_browser_dbfile: str,
) -> None:
    db = PhenoDb(
        fake_phenotype_data_dbfile,
    )
    assert db is not None

    measure_df = db.search_measures_df(None, "i")
    assert len(measure_df) == 15

    measure_df = db.search_measures_df(None, "i1")
    assert len(measure_df) == 12
    for _, row in measure_df.iterrows():
        assert row["instrument_name"] == "i1"


def test_db_search_character_escaping(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
        read_only=False,
    )
    assert db is not None

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

    db.save(val1)
    db.save(val2)

    res = db.search_measures_df(keyword="test_one")
    assert res is not None
    assert len(res) == 1
    assert res["measure_id"][0] == "test_one.measure1"
    assert res["instrument_name"][0] == "test_one"
    assert res["measure_name"][0] == "measure1"

    res = db.search_measures_df(keyword="test%two")
    assert res is not None
    assert len(res) == 1
    assert res["measure_id"][0] == "test%two.measure2"
    assert res["instrument_name"][0] == "test%two"
    assert res["measure_name"][0] == "measure2"


def test_get_regression_names(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
        read_only=False,
    )
    assert db is not None

    reg = {}
    reg["regression_id"] = "test_regression"
    reg["instrument_name"] = "test_instrument"
    reg["measure_name"] = "test_measure"
    reg["display_name"] = "a test regression with a display name"
    db.save_regression(reg)

    reg["regression_id"] = "test_regression2"
    reg["instrument_name"] = "test_instrument"
    reg["measure_name"] = "test_measure2"
    reg["display_name"] = "a second test regression with a display name"
    db.save_regression(reg)

    reg_names = db.regression_display_names
    assert reg_names == {
        "test_regression": "a test regression with a display name",
        "test_regression2": "a second test regression with a display name",
    }


def test_regression_ids(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
        read_only=False,
    )
    assert db is not None

    reg = {}

    reg["regression_id"] = "test_regression_1"
    reg["instrument_name"] = "test"
    reg["measure_name"] = "regressor1"
    db.save_regression(reg)

    reg["regression_id"] = "test_regression_2"
    reg["instrument_name"] = "test"
    reg["measure_name"] = "regressor2"
    db.save_regression(reg)

    reg_ids = db.regression_ids
    assert reg_ids == ["test_regression_1", "test_regression_2"]


def test_pheno_db_disabled(fake_pheno_db: PhenoRegistry) -> None:
    assert not fake_pheno_db.has_phenotype_data("fake_disabled")


def test_split_into_groups(fake_phenodb_file_copy: str) -> None:
    db = PhenoDb(
        fake_phenodb_file_copy,
    )
    measures = [f"measure_{i}" for i in range(1, 101)]
    groups = db._split_measures_into_groups(measures)
    assert len(groups) == 2
    assert len(groups[0]) == 60
    assert groups[0][0] == "measure_1"
    assert groups[0][-1] == "measure_60"
    assert len(groups[1]) == 40
    assert groups[1][0] == "measure_61"
    assert groups[1][-1] == "measure_100"

    groups = db._split_measures_into_groups(
        measures, group_size=25,
    )
    assert len(groups) == 4
    assert len(groups[0]) == 25
    assert groups[0][0] == "measure_1"
    assert groups[0][-1] == "measure_25"
    assert len(groups[1]) == 25
    assert groups[1][0] == "measure_26"
    assert groups[1][-1] == "measure_50"
    assert len(groups[2]) == 25
    assert groups[2][0] == "measure_51"
    assert groups[2][-1] == "measure_75"
    assert len(groups[3]) == 25
    assert groups[3][0] == "measure_76"
    assert groups[3][-1] == "measure_100"
