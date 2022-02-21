# """
# Created on Aug 31, 2017

# @author: lubo
# """
import os
from dae.pheno.db import DbManager


def test_db_save(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None

    print(db.browser_dbfile)
    db.build()

    v = {
        "measure_id": "test.measure",
        "instrument_name": "test",
        "measure_name": "measure",
        "measure_type": "other",
        "description": "desc",
    }

    db.save(v)

    r = db.get_browser_measure("test.measure")
    assert r is not None
    assert r.measure_id == "test.measure"
    assert r.instrument_name == "test"
    assert r.measure_name == "measure"
    assert r.figure_distribution is None


def test_db_update(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    v = {
        "measure_id": "test.measure",
        "instrument_name": "test",
        "measure_name": "measure",
        "measure_type": "other",
        "description": "desc",
    }
    print(v)
    db.save(v)
    print(v)
    v["measure_id"] = "test.measure"
    v["figure_distribution"] = "test_figure.png"
    db.save(v)

    r = db.get("test.measure")
    assert r is not None
    assert r.measure_id == "test.measure"
    assert r.instrument_name == "test"
    assert r.measure_name == "measure"
    assert r.figure_distribution == "test_figure.png"


def test_has_descriptions(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    for i in range(0, 3):
        v = {
            "measure_id": "test.measure{}".format(i),
            "instrument_name": "test",
            "measure_name": "measure{}".format(i),
            "measure_type": "other",
            "description": None,
        }
        db.save(v)
    assert not db.has_descriptions

    v = {
        "measure_id": "test.measure4",
        "instrument_name": "test",
        "measure_name": "measure4",
        "measure_type": "other",
        "description": "a description",
    }
    db.save(v)
    assert db.has_descriptions


def test_search_measures_get_all(
    fake_phenotype_data_dbfile, fake_phenotype_data_browser_dbfile
):
    db = DbManager(
        fake_phenotype_data_dbfile,
        fake_phenotype_data_browser_dbfile
    )
    assert db is not None
    db.build()
    assert len(list(db.search_measures())) == 15


def test_search_measures_get_by_instrument(
    fake_phenotype_data_dbfile, fake_phenotype_data_browser_dbfile
):
    db = DbManager(
        fake_phenotype_data_dbfile,
        fake_phenotype_data_browser_dbfile
    )
    assert db is not None
    db.build()
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
    fake_phenotype_data_dbfile, fake_phenotype_data_browser_dbfile
):
    db = DbManager(
        fake_phenotype_data_dbfile,
        fake_phenotype_data_browser_dbfile
    )
    assert db is not None
    db.build()
    measure_df = db.search_measures_df(None, "number")
    assert len(measure_df) == 3
    for _, row in measure_df.iterrows():
        assert "number" in row["description"]


def test_search_measures_by_keyword_in_measure_id(
    fake_phenotype_data_dbfile, fake_phenotype_data_browser_dbfile
):
    db = DbManager(
        fake_phenotype_data_dbfile,
        fake_phenotype_data_browser_dbfile
    )
    assert db is not None
    db.build()
    measure_df = db.search_measures_df(None, "i1.m2")
    assert len(measure_df) == 1
    assert measure_df.iloc[0]["measure_name"] == "m2"
    assert measure_df.iloc[0]["instrument_name"] == "i1"


def test_search_measures_by_keyword_in_measure_name(
    fake_phenotype_data_dbfile, fake_phenotype_data_browser_dbfile
):
    db = DbManager(
        fake_phenotype_data_dbfile,
        fake_phenotype_data_browser_dbfile
    )
    assert db is not None
    db.build()
    measure_df = db.search_measures_df(None, "m2")
    assert len(measure_df) == 2
    assert measure_df.iloc[0]["measure_name"] == "m2"
    assert measure_df.iloc[0]["instrument_name"] == "i1"
    assert measure_df.iloc[1]["measure_name"] == "m2"
    assert measure_df.iloc[1]["instrument_name"] == "i2"


def test_search_measures_by_keyword_in_instrument_name(
    fake_phenotype_data_dbfile, fake_phenotype_data_browser_dbfile
):
    db = DbManager(
        fake_phenotype_data_dbfile,
        fake_phenotype_data_browser_dbfile
    )
    assert db is not None
    db.build()

    measure_df = db.search_measures_df(None, "i")
    assert len(measure_df) == 15

    measure_df = db.search_measures_df(None, "i1")
    assert len(measure_df) == 12
    for _, row in measure_df.iterrows():
        assert row["instrument_name"] == "i1"


def test_db_search_character_escaping(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    v = {
        "measure_id": "test_one.measure1",
        "instrument_name": "test_one",
        "measure_name": "measure1",
        "measure_type": "other",
        "description": "desc",
    }

    v2 = {
        "measure_id": "test%two.measure2",
        "instrument_name": "test%two",
        "measure_name": "measure2",
        "measure_type": "other",
        "description": "desc",
    }

    db.save(v)
    db.save(v2)

    r = db.search_measures_df(keyword="test_one")
    assert r is not None
    assert len(r) == 1
    assert r["measure_id"][0] == "test_one.measure1"
    assert r["instrument_name"][0] == "test_one"
    assert r["measure_name"][0] == "measure1"

    r = db.search_measures_df(keyword="test%two")
    assert r is not None
    assert len(r) == 1
    assert r["measure_id"][0] == "test%two.measure2"
    assert r["instrument_name"][0] == "test%two"
    assert r["measure_name"][0] == "measure2"


def test_save_and_get_regressions(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    r = {}
    r["regression_id"] = "test_regression"
    r["instrument_name"] = "test_instrument"
    r["measure_name"] = "test_measure"
    r["display_name"] = "a test regression with a display name"
    db.save_regression(r)

    r["regression_id"] = "test_regression2"
    r["instrument_name"] = "test_instrument"
    r["measure_name"] = "test_measure2"
    del r["display_name"]
    db.save_regression(r)

    reg = db.get_regression("test_regression")
    assert reg is not None
    assert reg["regression_id"] == "test_regression"
    assert reg["instrument_name"] == "test_instrument"
    assert reg["measure_name"] == "test_measure"
    assert reg["display_name"] == "a test regression with a display name"

    reg = db.get_regression("test_regression2")
    assert reg is not None
    assert reg["regression_id"] == "test_regression2"
    assert reg["instrument_name"] == "test_instrument"
    assert reg["measure_name"] == "test_measure2"
    assert reg["display_name"] is None


def test_get_regression_names(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    r = {}
    r["regression_id"] = "test_regression"
    r["instrument_name"] = "test_instrument"
    r["measure_name"] = "test_measure"
    r["display_name"] = "a test regression with a display name"
    db.save_regression(r)

    r["regression_id"] = "test_regression2"
    r["instrument_name"] = "test_instrument"
    r["measure_name"] = "test_measure2"
    r["display_name"] = "a second test regression with a display name"
    db.save_regression(r)

    reg_names = db.regression_display_names
    assert reg_names == {
        "test_regression": "a test regression with a display name",
        "test_regression2": "a second test regression with a display name",
    }


def test_save_and_get_regression_values(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    regression_template = {
        "measure_id": "test.measure",
        "figure_regression": "regfigpath",
        "figure_regression_small": "regfigsmallpath",
    }
    r = regression_template

    r["regression_id"] = "test_regression_1"
    r["pvalue_regression_male"] = "0.1"
    r["pvalue_regression_female"] = "0.2"
    db.save_regression_values(r)

    r["regression_id"] = "test_regression_2"
    r["pvalue_regression_male"] = "0.3"
    r["pvalue_regression_female"] = "0.4"
    db.save_regression_values(r)

    reg = db.get_regression_values("test.measure")
    assert reg == [
        (
            "test_regression_1",
            "test.measure",
            "regfigpath",
            "regfigsmallpath",
            0.1,
            0.2,
        ),
        (
            "test_regression_2",
            "test.measure",
            "regfigpath",
            "regfigsmallpath",
            0.3,
            0.4,
        ),
    ]


def test_update_regression_values(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    regression_template = {
        "measure_id": "test.measure",
        "figure_regression": "regfigpath",
        "figure_regression_small": "regfigsmallpath",
    }
    r = regression_template

    r["regression_id"] = "test_regression_1"
    r["pvalue_regression_male"] = "0.1"
    r["pvalue_regression_female"] = "0.2"
    db.save_regression_values(r)

    reg = db.get_regression_values("test.measure")
    assert reg == [
        (
            "test_regression_1",
            "test.measure",
            "regfigpath",
            "regfigsmallpath",
            0.1,
            0.2,
        )
    ]

    r["pvalue_regression_male"] = "0.3"
    r["pvalue_regression_female"] = "0.4"
    db.save_regression_values(r)

    reg = db.get_regression_values("test.measure")
    assert reg == [
        (
            "test_regression_1",
            "test.measure",
            "regfigpath",
            "regfigsmallpath",
            0.3,
            0.4,
        )
    ]


def test_regression_ids(output_dir):
    db = DbManager(
        os.path.join(output_dir, "temp_testing.db"),
        browser_dbfile=os.path.join(output_dir, "temp_testing_browser.db")
    )
    assert db is not None
    db.build()

    r = {}

    r["regression_id"] = "test_regression_1"
    r["instrument_name"] = "test"
    r["measure_name"] = "regressor1"
    db.save_regression(r)

    r["regression_id"] = "test_regression_2"
    r["instrument_name"] = "test"
    r["measure_name"] = "regressor2"
    db.save_regression(r)

    reg_ids = db.regression_ids
    assert reg_ids == ["test_regression_1", "test_regression_2"]


def test_pheno_db_disabled(fake_pheno_db):
    assert not fake_pheno_db.has_phenotype_data("fake_disabled")
    assert len(fake_pheno_db.config) == 4
