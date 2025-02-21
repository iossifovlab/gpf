# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from typing import Any

import numpy as np
import pandas as pd
import pytest

from dae.pedigrees.family import Person
from dae.pheno.common import MeasureType
from dae.pheno.pheno_data import Measure, PhenotypeStudy
from dae.variants.attributes import Role


@pytest.fixture(scope="session")
def pheno_study(fake_phenotype_data: PhenotypeStudy) -> PhenotypeStudy:
    return fake_phenotype_data


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


def test_data_get_persons(pheno_study: PhenotypeStudy):
    persons = pheno_study.get_persons()
    assert persons is not None
    assert len(persons) == 195
    assert "f1.p1" in persons
    assert isinstance(persons["f1.p1"], Person)


def test_study_families(pheno_study: PhenotypeStudy):
    families = pheno_study.families
    assert families is not None
    assert len(families) == 39
    assert len(families.persons) == 195


def test_study_person_sets(pheno_study: PhenotypeStudy):
    person_set_collections = pheno_study.person_set_collections

    assert len(person_set_collections) == 1
    assert "phenotype" in person_set_collections

    assert len(person_set_collections["phenotype"].person_sets) == 2
    assert "autism" in person_set_collections["phenotype"].person_sets
    assert "unaffected" in person_set_collections["phenotype"].person_sets

    assert len(person_set_collections["phenotype"].person_sets["autism"]) == 66
    assert len(person_set_collections["phenotype"].person_sets["unaffected"]) == 129  # noqa: E501


def test_study_common_report(pheno_study: PhenotypeStudy):
    common_report = pheno_study.get_common_report()
    assert common_report is not None
    assert common_report.people_report is not None
    assert common_report.families_report is not None
    assert common_report.families_report.families_counters is not None


def test_get_measure_type(pheno_study: PhenotypeStudy) -> None:
    mes = pheno_study.get_measure("i1.m1")
    assert mes.measure_type == MeasureType.continuous


@pytest.mark.parametrize(
    "query_cols", [
        (["i1.m1"]),
        (["i1.m1", "i1.m2"]),
        (["i1.m1", "i2.m1"]),
    ],
)
def test_get_people_measure_values(
    pheno_study: PhenotypeStudy,
    query_cols: list[str],
) -> None:
    result_it = pheno_study.get_people_measure_values(query_cols)
    result = list(result_it)
    base_cols = ["person_id", "family_id", "role", "sex", "status"]
    db_query_cols = list(query_cols)
    dict_list_check(result, 195, base_cols + db_query_cols)

    result_it = pheno_study.get_people_measure_values(
        query_cols, ["f20.p1"])
    result = list(result_it)
    dict_list_check(result, 1, base_cols + db_query_cols)

    result_it = pheno_study.get_people_measure_values(
        query_cols, ["f20.p1", "f21.p1"])
    result = list(result_it)
    dict_list_check(result, 2, base_cols + db_query_cols)

    result_it = pheno_study.get_people_measure_values(
        query_cols, roles=[Role.prb])
    result = list(result_it)
    dict_list_check(result, 39, base_cols + db_query_cols)


def test_get_people_measure_values_non_overlapping(
    pheno_study: PhenotypeStudy,
) -> None:
    result_it = pheno_study.get_people_measure_values(
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


def test_get_people_measure_values_correct_values(
    pheno_study: PhenotypeStudy,
) -> None:
    result_list = list(pheno_study.get_people_measure_values(
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


def test_has_measure(pheno_study: PhenotypeStudy) -> None:
    measures = [
        "i1.m1",
        "i1.m2",
        "i1.m3",
        "i1.m4",
        "i1.m5",
        "i1.m6",
        "i1.m7",
        "i1.m8",
        "i1.m9",
        "i1.m10",
    ]
    assert all(pheno_study.has_measure(m) for m in measures)


def test_get_measures(pheno_study: PhenotypeStudy) -> None:
    measures = pheno_study.get_measures(
        measure_type=MeasureType.continuous,
    )
    assert len(measures) == 7


def test_get_query_with_dot_measure(
    pheno_study: PhenotypeStudy,
) -> None:
    result = pheno_study.db._get_measure_values_query(
        ["instr.some.measure.1"],
    )
    assert result is not None


@pytest.mark.parametrize(
    "families,expected_count", [(["f20"], 5), (["f20", "f21"], 10)],
)
@pytest.mark.parametrize("query_cols", [(["i1.m1"]), (["i1.m1", "i1.m2"])])
def test_get_values_families_filter(
    pheno_study: PhenotypeStudy,
    families: list[str],
    expected_count: int,
    query_cols: list[str],
) -> None:
    personlist = ["{}.dad", "{}.mom", "{}.p1"]
    vals = list(pheno_study.get_people_measure_values(
        query_cols, family_ids=families,
    ))
    all_people = [v["person_id"] for v in vals]
    for fam in families:
        assert all(p.format(fam) in all_people for p in personlist)
    base_cols = ["person_id", "family_id", "role", "sex", "status"]
    dict_list_check(vals, expected_count, base_cols + query_cols)


def test_min_max_measure_values(pheno_study: PhenotypeStudy) -> None:
    measures = pheno_study.get_measures()

    for measure in measures.values():
        if measure.measure_type in {MeasureType.categorical, MeasureType.raw}:
            continue
        mmin = measure.min_value
        mmax = measure.max_value
        df = pheno_study.get_people_measure_values_df(
            [measure.measure_id],
        )
        df = df[
            pd.to_numeric(df[measure.measure_id], errors="coerce").notna()
        ]
        error = np.abs(mmin - df[measure.measure_id].min())
        assert error < 1e-5, measure.measure_id

        error = np.abs(mmax - df[measure.measure_id].max())
        assert error < 1e-5, measure.measure_id


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
        "instrumentName": "i1",
        "measureType": "continuous",
        "description": "Measure number one",
        "defaultFilter": "",
        "valuesDomain": "[21.04639185188603, 131.3034132504469]",
        "minValue": pytest.approx(21.046, rel=1e-3),
        "maxValue": pytest.approx(131.303, rel=1e-3),
    }

    json = pheno_measure_categorical.to_json()
    assert json == {
        "measureName": "m5",
        "measureId": "i1.m5",
        "instrumentName": "i1",
        "measureType": "categorical",
        "description": "",
        "defaultFilter": "",
        "valuesDomain": "catA, catB, catC, catD, catF",
        "minValue": None,
        "maxValue": None,
    }
