# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from typing import Any, Callable, Generator

import pytest
import pandas as pd
import numpy as np

from dae.pheno.common import MeasureType
from dae.pheno.pheno_data import Measure, PhenotypeStudy
from dae.variants.attributes import Role


def df_check(
    df: pd.DataFrame, expected_count: int, expected_cols: list[str]
) -> None:
    assert df is not None
    # FIXME Should we drop na vals, and when?
    # df = df.dropna()
    assert all(col in df for col in expected_cols)
    assert expected_count == len(df)


def dict_gen_check(
    dict_gen: Generator[dict[str, Any], None, None],
    expected_count: int,
    expected_cols: list[str]
) -> None:
    dict_check(next(dict_gen), expected_count, expected_cols)


def dict_check(
    dict_: dict[str, Any], expected_count: int, expected_cols: list[str]
) -> None:
    assert isinstance(dict_, dict)
    for _person, measures in dict_.items():
        assert all(col in measures for col in expected_cols)
    assert expected_count == len(dict_)


def str_check(
    str_: str, expected_count: int, expected_cols: list[str]
) -> None:
    assert isinstance(str_, str)
    lines = str_.splitlines()
    header = lines[0]
    values_lines = lines[1:]
    columns = [col.strip() for col in header.split(",")]
    assert all(col in columns for col in expected_cols)
    assert len(values_lines) == expected_count


def dict_list_check(
    dict_list: list[dict[str, Any]],
    expected_count: int,
    expected_cols: list[str]
) -> None:
    assert isinstance(dict_list, list)
    for dict_ in dict_list:
        assert set(dict_.keys()) == set(expected_cols)
    assert len(dict_list) == expected_count


def dict_check_measure(
    dict_: dict[str, Measure],
    expected_count: int,
    *args: Any
) -> None:
    assert isinstance(dict_, dict)
    for _id, measure in dict_.items():
        assert isinstance(measure, Measure)
    assert expected_count == len(dict_)


def test_get_measure_type(fake_phenotype_data: PhenotypeStudy) -> None:
    mes = fake_phenotype_data.get_measure("i1.m1")
    assert mes.measure_type == MeasureType.continuous


@pytest.mark.parametrize(
    "query_cols", [
        (["i1.m1"]),
        (["i1.m1", "i1.m2"]),
        (["i1.m1", "i2.m2"])
    ]
)
def test_get_people_measure_values(
    fake_phenotype_data: PhenotypeStudy,
    query_cols: list[str]
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


def test_get_people_measure_values_non_overlapping(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    result_it = fake_phenotype_data.get_people_measure_values(
        ["i3.m1", "i4.m1"]
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
    fake_phenotype_data: PhenotypeStudy
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
        "i1.m2": pytest.approx(48.44644)
    }


def test_has_measure(fake_phenotype_data: PhenotypeStudy) -> None:
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
    assert all(fake_phenotype_data.has_measure(m) for m in measures)


@pytest.mark.parametrize(
    "get,check",
    [
        (PhenotypeStudy.get_measures, dict_check_measure),
        (PhenotypeStudy._get_measures_df, df_check),
    ],
)
def test_get_measures(
    fake_phenotype_data: PhenotypeStudy,
    get: Callable,
    check: Callable
) -> None:
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

    measures = get(fake_phenotype_data, measure_type=MeasureType.continuous)
    check(measures, 9, expected_cols)


def test_default_get_measure_df(fake_phenotype_data: PhenotypeStudy) -> None:
    df = fake_phenotype_data._get_measures_df()
    assert df is not None
    assert len(df) == 17


def test_get_persons_df(fake_phenotype_data: PhenotypeStudy) -> None:
    prbs = fake_phenotype_data.get_persons_df(roles=[Role.prb])
    assert len(prbs.columns) == 5
    df_check(prbs, 39, ["person_id", "family_id", "role", "sex", "status"])


@pytest.mark.parametrize(
    "families,expected_count", [(["f20"], 5), (["f20", "f21"], 10)]
)
@pytest.mark.parametrize("query_cols", [(["i1.m1"]), (["i1.m1", "i1.m2"])])
def test_get_values_families_filter(
    fake_phenotype_data: PhenotypeStudy,
    families: list[str],
    expected_count: int,
    query_cols: list[str]
) -> None:
    personlist = ["{}.dad", "{}.mom", "{}.p1"]
    vals = list(fake_phenotype_data.get_people_measure_values(
        query_cols, family_ids=families
    ))
    all_people = [v["person_id"] for v in vals]
    for fam in families:
        assert all(p.format(fam) in all_people for p in personlist)
    base_cols = ["person_id", "family_id", "role", "sex", "status"]
    dict_list_check(vals, expected_count, base_cols + query_cols)


def test_min_max_measure_values(fake_phenotype_data: PhenotypeStudy) -> None:
    measures = fake_phenotype_data.get_measures()

    for measure in measures.values():
        if measure.measure_type in {MeasureType.categorical, MeasureType.raw}:
            continue
        mmin = measure.min_value
        mmax = measure.max_value
        df = fake_phenotype_data.get_people_measure_values_df(
            [measure.measure_id]
        )
        df = df[
            pd.to_numeric(df[measure.measure_id], errors="coerce").notnull()
        ]
        error = np.abs(mmin - df[measure.measure_id].min())
        assert error < 1e-5, measure.measure_id

        error = np.abs(mmax - df[measure.measure_id].max())
        assert error < 1e-5, measure.measure_id


def test_get_persons_df_person_ids(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    res = fake_phenotype_data.get_persons_df(
        person_ids=[], family_ids=["f1", "f2", "f3"], roles=[Role.prb]
    )
    assert res.empty


def test_get_persons_df_family_ids(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    res = fake_phenotype_data.get_persons_df(
        person_ids=["f1.p1", "f2.p1", "f3.p1"], family_ids=[], roles=[Role.prb]
    )
    assert res.empty


def test_get_persons_df_roles(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    res = fake_phenotype_data.get_persons_df(
        person_ids=["f1.p1", "f2.p1", "f3.p1"],
        family_ids=["f1", "f2", "f3"],
        roles=[],
    )
    assert res.empty
