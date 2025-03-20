# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import os
from pathlib import Path
from typing import Any

import pytest
import pytest_mock

from dae.pedigrees.family import Person
from dae.pheno.common import ImportManifest, MeasureType, PhenoImportConfig
from dae.pheno.pheno_data import (
    Instrument,
    Measure,
    PhenotypeData,
    PhenotypeGroup,
    PhenotypeStudy,
    get_pheno_browser_images_dir,
    get_pheno_db_dir,
)
from dae.variants.attributes import Role


def _remove_common_report_cache(study: PhenotypeStudy):
    report_filename = study.config["common_report"]["file_path"]
    if os.path.exists(report_filename):
        os.remove(report_filename)


@pytest.fixture(scope="session", autouse=True)
def auto_setup_fixture(fake_phenotype_data: PhenotypeStudy):
    # Remove common_report.json if it was built. Done both before and
    # after a test has ran to ensure the file does not exist between tests.
    _remove_common_report_cache(fake_phenotype_data)
    yield
    _remove_common_report_cache(fake_phenotype_data)


@pytest.fixture(scope="session")
def pheno_measure_continuous(fake_phenotype_data: PhenotypeStudy) -> Measure:
    return fake_phenotype_data._measures["i1.m1"]


@pytest.fixture(scope="session")
def pheno_measure_categorical(fake_phenotype_data: PhenotypeStudy) -> Measure:
    return fake_phenotype_data._measures["i1.m5"]


def dict_list_check(
    dict_list: list[dict[str, Any]],
    expected_count: int,
    expected_cols: list[str],
) -> None:
    assert isinstance(dict_list, list)
    for dict_ in dict_list:
        assert set(dict_.keys()) == set(expected_cols)
    assert len(dict_list) == expected_count


def test_measure_domain(
    pheno_measure_continuous: Measure,
    pheno_measure_categorical: Measure,
) -> None:
    domain = pheno_measure_continuous.domain
    assert len(domain) == 2
    assert domain[0] == pytest.approx(21.046, rel=1e-3)
    assert domain[1] == pytest.approx(131.303, rel=1e-3)

    domain = pheno_measure_categorical.domain
    assert domain == ["catA", "catB", "catC", "catD", "catF"]


def test_measure_to_json(
    pheno_measure_continuous: Measure,
    pheno_measure_categorical: Measure,
) -> None:
    json = pheno_measure_continuous.to_json()
    assert json == {
        "measureName": "m1",
        "measureId": "i1.m1",
        "histogramType": "NumberHistogram",
        "valueType": "float",
        "instrumentName": "i1",
        "measureType": "continuous",
        "description": "Measure number one",
        "defaultFilter": "",
        "histogramConfig": None,
        "valuesDomain": "[21.04639185188603, 131.3034132504469]",
        "minValue": pytest.approx(21.046, rel=1e-4),
        "maxValue": pytest.approx(131.303, rel=1e-4),
    }

    json = pheno_measure_categorical.to_json()
    assert json == {
        "measureName": "m5",
        "measureId": "i1.m5",
        "instrumentName": "i1",
        "measureType": "categorical",
        "histogramType": "CategoricalHistogram",
        "valueType": "str",
        "description": "",
        "defaultFilter": "",
        "histogramConfig": None,
        "valuesDomain": "catA, catB, catC, catD, catF",
        "minValue": None,
        "maxValue": None,
    }


def test_data_get_persons(fake_phenotype_data: PhenotypeStudy):
    persons = fake_phenotype_data.get_persons()
    assert persons is not None
    assert len(persons) == 195
    assert "f1.p1" in persons
    assert isinstance(persons["f1.p1"], Person)


def test_data_get_person_roles(fake_phenotype_data: PhenotypeStudy):
    roles = fake_phenotype_data.get_person_roles()
    assert roles is not None
    assert roles == ["dad", "mom", "prb", "sib"]


def test_data_get_measure(fake_phenotype_data: PhenotypeStudy) -> None:
    mes = fake_phenotype_data.get_measure("i1.m1")
    assert mes is not None
    assert mes.measure_type == MeasureType.continuous


def test_data_get_measures(fake_phenotype_data: PhenotypeStudy) -> None:
    measures = fake_phenotype_data.get_measures(
        measure_type=MeasureType.continuous,
    )
    assert len(measures) == 7


def test_data_has_measure(fake_phenotype_data: PhenotypeStudy) -> None:
    measures = [
        "i1.m1", "i1.m2", "i1.m3", "i1.m4", "i1.m5",
        "i1.m6", "i1.m7", "i1.m8", "i1.m9", "i1.m10",
    ]
    assert all(fake_phenotype_data.has_measure(m) for m in measures)


def test_data_get_measure_description(fake_phenotype_data: PhenotypeStudy):
    assert fake_phenotype_data.get_measure_description("i1.m1") == {
        "instrument_name": "i1",
        "measure_name": "m1",
        "measure_type": "continuous",
        "values_domain": [pytest.approx(21.046, rel=1e-3),
                          pytest.approx(131.303, rel=1e-3)],
        "min_value": pytest.approx(21.046, rel=1e-3),
        "max_value": pytest.approx(131.303, rel=1e-3),
    }
    assert fake_phenotype_data.get_measure_description("i1.m5") == {
        "instrument_name": "i1",
        "measure_name": "m5",
        "measure_type": "categorical",
        "values_domain": ["catA", "catB", "catC", "catD", "catF"],
    }


def test_data_get_instruments(fake_phenotype_data: PhenotypeStudy) -> None:
    assert fake_phenotype_data.get_instruments() == ["i1", "i2", "i3", "i4"]


def test_data_get_instrument_measures(fake_phenotype_data: PhenotypeStudy):
    assert fake_phenotype_data.get_instrument_measures("i1") == [
        "i1.age", "i1.iq", "i1.m1", "i1.m2", "i1.m3", "i1.m4",
        "i1.m5", "i1.m6", "i1.m7", "i1.m8", "i1.m9", "i1.m10",
    ]


def test_data_get_person_set_collection(fake_phenotype_data: PhenotypeStudy):
    assert fake_phenotype_data\
        .get_person_set_collection("phenotype") is not None
    assert fake_phenotype_data\
        .get_person_set_collection("nonexistent") is None
    assert fake_phenotype_data\
        .get_person_set_collection(None) is None


def test_data_create_browser(fake_phenotype_data: PhenotypeStudy) -> None:
    browser = PhenotypeData.create_browser(fake_phenotype_data)
    assert browser is not None


def test_data_browser_property(fake_phenotype_data: PhenotypeStudy) -> None:
    assert fake_phenotype_data._browser is None
    browser = fake_phenotype_data.browser
    assert browser is not None
    assert fake_phenotype_data._browser is not None


def test_data_is_browser_outdated(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    browser = fake_phenotype_data.browser
    assert browser is not None
    is_outdated = fake_phenotype_data.is_browser_outdated(browser)
    assert is_outdated is False


def test_data_is_browser_outdated_older(
    fake_phenotype_data: PhenotypeStudy,
    mocker: pytest_mock.MockerFixture,
) -> None:
    import_manifest = fake_phenotype_data.generate_import_manifests()[0]
    # this is the browser manifest's timestamp + 1, hardcoded
    # cause writing it dynamically will bloat the test further.
    # update this value if the browser db file is re-built.
    import_manifest.unix_timestamp = 1739974139 + 1

    mocker.patch(
        "dae.pheno.pheno_data.PhenotypeStudy.generate_import_manifests",
        return_value=[import_manifest],
    )
    browser = fake_phenotype_data.browser
    assert browser is not None
    is_outdated = fake_phenotype_data.is_browser_outdated(browser)
    assert is_outdated is True


def test_data_is_browser_outdated_no_browser_manifests(
    fake_phenotype_data: PhenotypeStudy,
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch(
        "dae.pheno.common.ImportManifest.from_table",
        return_value=[],
    )
    browser = fake_phenotype_data.browser
    assert browser is not None
    is_outdated = fake_phenotype_data.is_browser_outdated(browser)
    assert is_outdated is True


def test_data_is_browser_outdated_count_mismatch(
    fake_phenotype_data: PhenotypeStudy,
    mocker: pytest_mock.MockerFixture,
) -> None:

    mock_import_config_a = PhenoImportConfig.model_validate({
        "id": "a",
        "input_dir": "a",
        "work_dir": "a",
        "instrument_files": ["a"],
        "pedigree": "a",
        "person_column": "a",
    })
    mock_import_config_b = PhenoImportConfig.model_validate({
        "id": "b",
        "input_dir": "b",
        "work_dir": "b",
        "instrument_files": ["b"],
        "pedigree": "b",
        "person_column": "b",
    })

    mocker.patch(
        "dae.pheno.pheno_data.PhenotypeStudy.generate_import_manifests",
        return_value=[
            ImportManifest(unix_timestamp=1,
                           import_config=mock_import_config_a),
            ImportManifest(unix_timestamp=1,
                           import_config=mock_import_config_b),
        ],
    )
    browser = fake_phenotype_data.browser
    assert browser is not None
    is_outdated = fake_phenotype_data.is_browser_outdated(browser)
    assert is_outdated is True


def test_study_families(fake_phenotype_data: PhenotypeStudy):
    families = fake_phenotype_data.families
    assert families is not None
    assert len(families) == 39
    assert len(families.persons) == 195


def test_study_person_sets(fake_phenotype_data: PhenotypeStudy):
    person_set_collections = fake_phenotype_data.person_set_collections

    assert len(person_set_collections) == 1
    assert "phenotype" in person_set_collections

    assert len(person_set_collections["phenotype"].person_sets) == 2
    assert "autism" in person_set_collections["phenotype"].person_sets
    assert "unaffected" in person_set_collections["phenotype"].person_sets

    assert len(person_set_collections["phenotype"].person_sets["autism"]) == 66
    assert len(person_set_collections["phenotype"].person_sets["unaffected"]) == 129  # noqa: E501


def test_study_common_report(fake_phenotype_data: PhenotypeStudy):
    common_report = fake_phenotype_data.get_common_report()
    assert common_report is not None
    assert common_report.people_report is not None
    assert common_report.families_report is not None
    assert common_report.families_report.families_counters is not None


def test_study_get_children_ids(fake_phenotype_data: PhenotypeStudy):
    assert fake_phenotype_data.get_children_ids() == ["fake"]


@pytest.mark.parametrize(
    "query_cols", [
        (["i1.m1"]),
        (["i1.m1", "i1.m2"]),
        (["i1.m1", "i2.m1"]),
    ],
)
def test_study_get_people_measure_values(
    fake_phenotype_data: PhenotypeStudy,
    query_cols: list[str],
) -> None:
    result_it = fake_phenotype_data.get_people_measure_values(query_cols)
    result = list(result_it)
    base_cols = ["person_id", "family_id", "role", "sex", "status"]
    db_query_cols = list(query_cols)
    dict_list_check(result, 195, base_cols + db_query_cols)

    result_it = fake_phenotype_data.get_people_measure_values(
        query_cols, ["f20.p1"])
    result = list(result_it)
    dict_list_check(result, 1, base_cols + db_query_cols)

    result_it = fake_phenotype_data.get_people_measure_values(
        query_cols, ["f20.p1", "f21.p1"])
    result = list(result_it)
    dict_list_check(result, 2, base_cols + db_query_cols)

    result_it = fake_phenotype_data.get_people_measure_values(
        query_cols, roles=[Role.prb])
    result = list(result_it)
    dict_list_check(result, 39, base_cols + db_query_cols)


def test_study_get_people_measure_values_non_overlapping(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    result_it = fake_phenotype_data.get_people_measure_values(
        ["i3.m1", "i4.m1"],
    )
    result = list(result_it)
    assert len(result) == 9

    assert result[0]["person_id"] == "f1.dad"
    assert result[0]["i3.m1"] == 1.0
    assert result[0]["i4.m1"] is None

    assert result[1]["person_id"] == "f1.mom"
    assert result[1]["i3.m1"] is None
    assert result[1]["i4.m1"] == 1.0

    assert result[2]["person_id"] == "f1.p1"
    assert result[2]["i3.m1"] is None
    assert result[2]["i4.m1"] == 1.0

    assert result[3]["person_id"] == "f1.s1"
    assert result[3]["i3.m1"] == 1.0
    assert result[3]["i4.m1"] is None

    assert result[4]["person_id"] == "f1.s2"
    assert result[4]["i3.m1"] == 1.0
    assert result[4]["i4.m1"] is None

    assert result[5]["person_id"] == "f2.dad"
    assert result[5]["i3.m1"] == 1.0
    assert result[5]["i4.m1"] is None

    assert result[6]["person_id"] == "f2.mom"
    assert result[6]["i3.m1"] is None
    assert result[6]["i4.m1"] == 1.0

    assert result[7]["person_id"] == "f2.p1"
    assert result[7]["i3.m1"] is None
    assert result[7]["i4.m1"] == 1.0

    assert result[8]["person_id"] == "f2.s1"
    assert result[8]["i3.m1"] == 1.0
    assert result[8]["i4.m1"] is None


def test_study_get_people_measure_values_correct_values(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    result_list = list(fake_phenotype_data.get_people_measure_values(
        ["i1.m1", "i1.m2"], roles=[Role.prb]))
    assert result_list[0] == {
        "person_id": "f1.p1",
        "family_id": "f1",
        "role": "prb",
        "sex": "M",
        "status": "affected",
        "i1.m1": pytest.approx(34.76286),
        "i1.m2": pytest.approx(48.44644),
    }


@pytest.mark.parametrize(
    "families,expected_count", [(["f20"], 5), (["f20", "f21"], 10)],
)
@pytest.mark.parametrize("query_cols", [(["i1.m1"]), (["i1.m1", "i1.m2"])])
def test_study_get_values_families_filter(
    fake_phenotype_data: PhenotypeStudy,
    families: list[str],
    expected_count: int,
    query_cols: list[str],
) -> None:
    personlist = ["{}.dad", "{}.mom", "{}.p1"]
    vals = list(fake_phenotype_data.get_people_measure_values(
        query_cols, family_ids=families,
    ))
    all_people = [v["person_id"] for v in vals]
    for fam in families:
        assert all(p.format(fam) in all_people for p in personlist)
    base_cols = ["person_id", "family_id", "role", "sex", "status"]
    dict_list_check(vals, expected_count, base_cols + query_cols)


def test_study_generate_import_manifests(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    manifests = fake_phenotype_data.generate_import_manifests()
    assert manifests is not None
    assert len(manifests) == 1
    assert isinstance(manifests[0], ImportManifest)


def test_study_get_regressions(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    assert fake_phenotype_data.get_regressions() == {
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


def test_study_get_measures_info(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    assert fake_phenotype_data.get_measures_info() == {
        "base_image_url": "static/images/",
        "has_descriptions": True,
        "regression_names": {
            "age": "age",
            "nviq": "nonverbal iq",
        },
    }


def test_study_search_measures(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    res = list(fake_phenotype_data.search_measures("i1", "m1"))
    assert len(res) == 2
    assert res[0]["measure"]["measure_id"] == "i1.m1"
    assert res[1]["measure"]["measure_id"] == "i1.m10"

    measure = res[0]["measure"]
    assert measure["measure_type"] == "continuous"
    assert len(measure["regressions"]) > 0
    reg = measure["regressions"][0]
    assert "figure_regression" in reg
    assert "figure_regression_small" in reg
    assert "pvalue_regression_male" in reg
    assert "pvalue_regression_female" in reg


def test_study_count_measures(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    assert fake_phenotype_data.count_measures(None, None) == 15


def test_group_init(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert fake_phenotype_group is not None


def test_group_merge_instruments() -> None:
    i1 = Instrument("i1")
    i2 = Instrument("i2")
    i1.measures["m1"] = Measure("m1", "measure 1")
    i2.measures["m1"] = Measure("m1", "measure 1")
    res_instruments, res_measures = PhenotypeGroup._merge_instruments(
        ({"i1": i1}, {"i2": i2}),
    )
    assert len(res_instruments) == 2
    assert "i1" in res_instruments
    assert "m1" in res_instruments["i1"].measures
    assert "i2" in res_instruments
    assert "m1" in res_instruments["i2"].measures
    assert len(res_measures) == 2
    assert "i1.m1" in res_measures
    assert "i2.m1" in res_measures


def test_group_merge_instruments_duplicate() -> None:
    i1 = Instrument("i1")
    i1.measures["m1"] = Measure("m1", "measure 1")
    with pytest.raises(ValueError, match="measure duplication"):
        PhenotypeGroup._merge_instruments(
            ({"i1": i1}, {"i1": i1}),
        )


def test_group_leaves(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert len(fake_phenotype_group.get_leaves()) == 2


def test_group_generate_import_manifests(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert len(fake_phenotype_group.generate_import_manifests()) == 2


def test_group_get_children_ids(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert fake_phenotype_group.get_children_ids() == [
        "fake", "fake2",
    ]
    assert fake_phenotype_group.get_children_ids(leaves=False) == [
        "fake", "fake_subgroup",
    ]


def test_group_get_regressions(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert len(fake_phenotype_group.get_regressions()) == 2


def test_group_get_measures_info(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert fake_phenotype_group.get_measures_info() == {
        "base_image_url": "static/images/",
        "has_descriptions": True,
        "regression_names": {
            "age": "age",
            "nviq": "nonverbal iq",
        },
    }


def test_group_search_measures(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert len(list(fake_phenotype_group.search_measures(None, "m1"))) == 7


def test_group_count_measures(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    assert fake_phenotype_group.count_measures(None, None) == 27


def test_group_get_people_measure_values(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    res = list(fake_phenotype_group.get_people_measure_values(["i1.m1"]))
    assert len(res) == 195


def test_group_get_people_measure_values_df(
    fake_phenotype_group: PhenotypeGroup,
) -> None:
    res = fake_phenotype_group.get_people_measure_values_df(["i1.m1"])
    assert list(res) == ["person_id", "family_id", "role",
                         "status", "sex", "i1.m1"]
    assert len(res) == 195


def test_get_query_with_dot_measure(
    fake_phenotype_data: PhenotypeStudy,
) -> None:
    result = fake_phenotype_data.db._get_measure_values_query(
        ["instr.some.measure.1"],
    )
    assert result is not None


def test_get_pheno_db_dir(
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch.dict(os.environ, {"DAE_DB_DIR": "mock_dae_dir"})
    res = get_pheno_db_dir(None)
    assert res == "mock_dae_dir/pheno"

    res = get_pheno_db_dir({
        "conf_dir": "mock",
    })
    assert res == "mock/pheno"

    res = get_pheno_db_dir({
        "conf_dir": "mock",
        "phenotype_data": {"dir": None},
    })
    assert res == "mock/pheno"

    res = get_pheno_db_dir({
        "conf_dir": "mock",
        "phenotype_data": {"dir": "blabla_pheno_dir"},
    })
    assert res == "blabla_pheno_dir"


def test_get_pheno_browser_images_dir(
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch.dict(os.environ, {"DAE_DB_DIR": "mock_dae_dir"})
    res = get_pheno_browser_images_dir()
    assert res == Path("mock_dae_dir", "pheno", "images")

    res = get_pheno_browser_images_dir({
        "conf_dir": "mock",
    })
    assert res == Path("mock", "pheno", "images")

    res = get_pheno_browser_images_dir({
        "conf_dir": "mock",
        "phenotype_images": "mock/bla",
    })
    assert res == Path("mock", "bla")

    res = get_pheno_browser_images_dir({
        "conf_dir": "mock",
        "cache_path": "mock/cache",
    })
    assert res == Path("mock", "cache", "images")
