# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
import pandas as pd
import numpy as np
from dae.pheno.common import MeasureType
from dae.pheno.pheno_db import Measure, PhenotypeStudy


def df_check(df, expected_count, expected_cols):
    assert df is not None
    # FIXME Should we drop na vals, and when?
    # df = df.dropna()
    assert all([col in df for col in expected_cols])
    assert expected_count == len(df)


def dict_check(dict_, expected_count, expected_cols):
    assert isinstance(dict_, dict)
    for _person, measures in dict_.items():
        assert all(col in measures for col in expected_cols)
    assert expected_count == len(dict_)


def str_check(str_, expected_count, expected_cols):
    assert isinstance(str_, str)
    lines = str_.splitlines()
    header = lines[0]
    values_lines = lines[1:]
    columns = [col.strip() for col in header.split(",")]
    assert all([col in columns for col in expected_cols])
    assert len(values_lines) == expected_count


def dict_list_check(dict_list, expected_count, expected_cols):
    assert isinstance(dict_list, list)
    for dict_ in dict_list:
        assert set(dict_.keys()) == set(expected_cols)
    assert len(dict_list) == expected_count


def dict_check_measure(dict_, expected_count, *args):
    assert isinstance(dict_, dict)
    for _id, measure in dict_.items():
        assert isinstance(measure, Measure)
    assert expected_count == len(dict_)


def test_get_measure_type(fake_phenotype_data):
    mes = fake_phenotype_data.get_measure("i1.m1")
    assert mes.measure_type == MeasureType.continuous


@pytest.mark.parametrize("query_cols", [(["i1.m1"]), (["i1.m1", "i1.m2"])])
@pytest.mark.parametrize(
    "get,check",
    [
        (PhenotypeStudy.get_values, dict_check),
        (PhenotypeStudy.get_values_df, df_check),
    ],
)
def test_get_values(fake_phenotype_data, query_cols, get, check):
    vals = get(fake_phenotype_data, query_cols)
    check(vals, 195, query_cols)

    vals = get(fake_phenotype_data, query_cols, ["f20.p1"])
    check(vals, 1, query_cols)

    vals = get(fake_phenotype_data, query_cols, ["f20.p1", "f21.p1"])
    check(vals, 2, query_cols)

    vals = get(fake_phenotype_data, query_cols, roles=["prb"])
    check(vals, 39, query_cols)


@pytest.mark.parametrize("query_cols", [(["i1.m1"]), (["i1.m1", "i1.m2"])])
def test_get_people_measure_values(fake_phenotype_data, query_cols):
    result_it = fake_phenotype_data.get_people_measure_values(query_cols)
    result = list(result_it)
    dict_list_check(result, 195, ["person_id"] + query_cols)

    result_it = fake_phenotype_data.get_people_measure_values(
        query_cols, ["f20.p1"])
    result = list(result_it)
    dict_list_check(result, 1, ["person_id"] + query_cols)

    result_it = fake_phenotype_data.get_people_measure_values(
        query_cols, ["f20.p1", "f21.p1"])
    result = list(result_it)
    dict_list_check(result, 2, ["person_id"] + query_cols)

    result_it = fake_phenotype_data.get_people_measure_values(
        query_cols, roles=["prb"])
    result = list(result_it)
    dict_list_check(result, 39, ["person_id"] + query_cols)


def test_get_people_measure_values_correct_values(fake_phenotype_data):
    result_list = list(fake_phenotype_data.get_people_measure_values(
        ["i1.m1", "i1.m2"], roles=["prb"]))
    assert result_list[-1] == {
        "person_id": "f1.p1",
        "i1.m1": 34.76285793898369,
        "i1.m2": 48.44644402952317
    }


def test_split_into_groups(fake_phenotype_data):
    measures = [f"measure_{i}" for i in range (1, 101)]
    groups = fake_phenotype_data._split_measures_into_groups(measures)
    assert len(groups) == 2
    assert len(groups[0]) == 60
    assert groups[0][0] == "measure_1"
    assert groups[0][-1] == "measure_60"
    assert len(groups[1]) == 40
    assert groups[1][0] == "measure_61"
    assert groups[1][-1] == "measure_100"

    groups = fake_phenotype_data._split_measures_into_groups(
        measures, group_size=25
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


def test_subquery_generation(fake_phenotype_data):
    fake_measures_ids = {
        "i1.m1": "1",
        "i1.m2": "2"
    }
    query = str(fake_phenotype_data._build_measures_subquery(
        fake_measures_ids,
        fake_measures_ids.keys(),
        person_ids=["person1", "person2"],
        family_ids=["family1"],
        roles=["unaffected"]
    ))

    print(query)
    expected = (
        "SELECT person.person_id, \"i1.m1_value\".value AS 'i1.m1', "
        "\"i1.m2_value\".value AS 'i1.m2' \n"
        "FROM person JOIN family ON family.id = person.family_id "
        'LEFT OUTER JOIN value_continuous as "i1.m1_value" '
        'ON "i1.m1_value".person_id = person.id '
        'AND "i1.m1_value".measure_id = 1 '
        'LEFT OUTER JOIN value_continuous as "i1.m2_value" '
        'ON "i1.m2_value".person_id = person.id '
        'AND "i1.m2_value".measure_id = 2 \n'
        "WHERE person.role IN (__[POSTCOMPILE_role_1]) "
        "AND person.person_id IN (__[POSTCOMPILE_person_id_1]) "
        "AND family.family_id IN (__[POSTCOMPILE_family_id_1]) "
        "ORDER BY person.person_id DESC"
    )
    assert query == expected


@pytest.mark.parametrize(
    "get,check",
    [
        (PhenotypeStudy.get_instrument_values, dict_check),
        (PhenotypeStudy.get_instrument_values_df, df_check),
    ],
)
def test_get_instrument_values(fake_phenotype_data, get, check):
    values = get(fake_phenotype_data, "i1")
    check(
        values,
        195,
        [
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
        ],
    )


def test_has_measure(fake_phenotype_data):
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
    assert all([fake_phenotype_data.has_measure(m) for m in measures])


@pytest.mark.parametrize(
    "get,check",
    [
        (PhenotypeStudy.get_measures, dict_check_measure),
        (PhenotypeStudy._get_measures_df, df_check),
    ],
)
def test_get_measures(fake_phenotype_data, get, check):
    expected_cols = [
        "measure_id",
        "measure_name",
        "instrument_name",
        "description",
        "individuals",
        "measure_type",
        "min_value",
        "max_value",
        "values_domain",
    ]

    measures = get(fake_phenotype_data, measure_type="continuous")
    check(measures, 7, expected_cols)


def test_default_get_measure_df(fake_phenotype_data):
    df = fake_phenotype_data._get_measures_df()
    assert df is not None
    assert len(df) == 15


def test_get_persons_df(fake_phenotype_data):
    prbs = fake_phenotype_data.get_persons_df(roles=["prb"])
    assert len(prbs.columns) == 5
    df_check(prbs, 39, ["person_id", "family_id", "role", "sex", "status"])


def test_get_persons_values_df(fake_phenotype_data):
    pvdf = fake_phenotype_data.get_persons_values_df(["i1.m1"])
    assert len(pvdf) > 0


@pytest.mark.parametrize(
    "families,expected_count", [(["f20"], 5), (["f20", "f21"], 10)]
)
@pytest.mark.parametrize("query_cols", [(["i1.m1"]), (["i1.m1", "i1.m2"])])
def test_get_values_families_filter(
    fake_phenotype_data, families, expected_count, query_cols
):
    personlist = ["{}.dad", "{}.mom", "{}.p1"]
    vals = fake_phenotype_data.get_values(query_cols, family_ids=families)
    for fam in families:
        assert all(p.format(fam) in vals for p in personlist)
    dict_check(vals, expected_count, query_cols)


def test_min_max_measure_values(fake_phenotype_data):
    measures = fake_phenotype_data.get_measures()

    for measure in measures.values():
        if (
            measure.measure_type == MeasureType.categorical
            or measure.measure_type == MeasureType.raw
        ):
            continue
        mmin = measure.min_value
        mmax = measure.max_value
        df = fake_phenotype_data.get_measure_values_df(
            measure.measure_id, default_filter="skip"
        )
        df = df[
            pd.to_numeric(df[measure.measure_id], errors="coerce").notnull()
        ]
        error = np.abs(mmin - df[measure.measure_id].min())
        assert error < 1e-5, measure.measure_id

        error = np.abs(mmax - df[measure.measure_id].max())
        assert error < 1e-5, measure.measure_id


def test_get_persons_df_person_ids(fake_phenotype_data):
    res = fake_phenotype_data.get_persons_df(
        person_ids=[], family_ids=["f1", "f2", "f3"], roles=["prb"]
    )
    assert res.empty


def test_get_persons_df_family_ids(fake_phenotype_data):
    res = fake_phenotype_data.get_persons_df(
        person_ids=["f1.p1", "f2.p1", "f3.p1"], family_ids=[], roles=["prb"]
    )
    assert res.empty


def test_get_persons_df_roles(fake_phenotype_data):
    res = fake_phenotype_data.get_persons_df(
        person_ids=["f1.p1", "f2.p1", "f3.p1"],
        family_ids=["f1", "f2", "f3"],
        roles=[],
    )
    assert res.empty


def test_raw_get_measure_values_df_person_ids(fake_phenotype_data):
    test_measure = fake_phenotype_data.get_measure("i1.m1")
    res = fake_phenotype_data._raw_get_measure_values_df(
        test_measure,
        person_ids=[],
        family_ids=["f1", "f2", "f3"],
        roles=["prb"],
    )
    assert res.empty


def test_raw_get_measure_values_df_family_ids(fake_phenotype_data):
    test_measure = fake_phenotype_data.get_measure("i1.m1")
    res = fake_phenotype_data._raw_get_measure_values_df(
        test_measure,
        person_ids=["f1.p1", "f2.p1", "f3.p1"],
        family_ids=[],
        roles=["prb"],
    )
    assert res.empty


def test_raw_get_measure_values_df_roles(fake_phenotype_data):
    test_measure = fake_phenotype_data.get_measure("i1.m1")
    res = fake_phenotype_data._raw_get_measure_values_df(
        test_measure,
        person_ids=["f1.p1", "f2.p1", "f3.p1"],
        family_ids=["f1", "f2", "f3"],
        roles=[],
    )
    assert res.empty
