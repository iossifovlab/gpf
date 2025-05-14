# pylint: disable=W0621,C0114,C0116,W0212,W0613
from collections import Counter

import numpy as np
import pandas as pd
import pytest
import pytest_mock

from dae.pheno.pheno_data import PhenotypeStudy
from dae.pheno_tool.tool import PhenoResult, PhenoTool
from dae.variants.attributes import Sex


def test_init_pheno_df(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(
        t4c8_study_1_pheno,
    )
    pheno_df = pheno_tool.create_df(
        "i1.m1",
        normalize_by=[{"instrument_name": "i1", "measure_name": "m2"}],
    )
    assert pheno_df is not None
    assert not pheno_df.empty
    assert set(pheno_df) == {
        "person_id",
        "family_id",
        "role",
        "status",
        "sex",
        "i1.m1",
        "i1.m2",
        "normalized",
    }


def test_init_empty_person_ids_normalize(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    pheno_df = pheno_tool.create_df(
        "i1.m1",
        person_ids=[],
        normalize_by=[{"instrument_name": "i1", "measure_name": "m2"}],
    )
    assert pheno_df is not None


def test_init_nonexistent_measure(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    with pytest.raises(KeyError):
        pheno_tool.create_df("i1.??")


def test_init_non_continuous_or_ordinal_measure(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    with pytest.raises(AssertionError):
        pheno_tool.create_df("i1.m5")  # categorical


def test_init_with_person_ids(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(
        t4c8_study_1_pheno,
    )
    pheno_df = pheno_tool.create_df(
        "i1.m1",
        person_ids=["p1", "p3", "p4", "p5", "p7"],
    )

    assert set(pheno_df["person_id"]) == {
        "p1", "p3", "p4"}


def test_init_normalize_measures(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    norm_measures_in = [
        {"measure_name": "??", "instrument_name": ""},
        {"measure_name": "m3", "instrument_name": ""},
        {"measure_name": "iq", "instrument_name": "i1"},
    ]

    norm_measures = pheno_tool.init_normalize_measures(
        "i1.m3", norm_measures_in,
    )
    assert len(norm_measures) == 1
    assert set(norm_measures) == {"i1.iq"}
    for measure_id in norm_measures:
        assert t4c8_study_1_pheno.has_measure(measure_id)


def test_init_normalize_measures_non_continuous(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    norm_measures = [
        {"measure_name": "??", "instrument_name": ""},
        {"measure_name": "m5", "instrument_name": ""},
        {"measure_name": "m7", "instrument_name": "i1"},
    ]
    with pytest.raises(AssertionError):
        pheno_tool.init_normalize_measures("i1.m1", norm_measures)


def test_get_normalize_measure_id_non_dict_measure(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    with pytest.raises(AssertionError):
        pheno_tool.get_normalize_measure_id(
            "i1.m1", ["measure"],  # type: ignore
        )
    with pytest.raises(AssertionError):
        pheno_tool.get_normalize_measure_id(
            "i1.m1", "measure",  # type: ignore
        )
    with pytest.raises(AssertionError):
        pheno_tool.get_normalize_measure_id(
            "i1.m1", None,  # type: ignore
        )


def test_get_normalize_measure_id_measure_dict_no_keys(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    with pytest.raises(AssertionError):
        pheno_tool.get_normalize_measure_id(
            "i1.m1", {"measure_name": "something"},
        )
    with pytest.raises(AssertionError):
        pheno_tool.get_normalize_measure_id(
            "i1.m1", {"instrument_name": "something"},
        )


def test_get_normalize_measure_id_no_instrument_name(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    measure_id = pheno_tool.get_normalize_measure_id(
        "i1.m1",
        {"measure_name": "m3", "instrument_name": None},  # type: ignore
    )
    assert measure_id == "i1.m3"


def test_get_normalize_measure_id_with_instrument_name(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    measure_id = pheno_tool.get_normalize_measure_id(
        "i1.m1",
        {"measure_name": "age", "instrument_name": "i1"},
    )
    assert measure_id == "i1.age"


def test_get_normalize_measure_id_same_measure(
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    measure_id = pheno_tool.get_normalize_measure_id(
        "i1.m1",
        {"measure_name": "m1", "instrument_name": "i1"},
    )
    assert measure_id is None


@pytest.mark.parametrize(
    "measure_name,instrument_name",
    [("??", "i1"), ("i1", "??"), ("??", "??"), ("??", None)],
)
def test_get_normalize_measure_id_non_existent(
    t4c8_study_1_pheno: PhenotypeStudy,
    measure_name: str,
    instrument_name: str | None,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    measure_id = pheno_tool.get_normalize_measure_id(
        "i1.m1",
        {"measure_name": measure_name,
         "instrument_name": instrument_name},  # type: ignore
    )
    assert measure_id is None


def test_join_pheno_df_with_variants() -> None:
    pheno_df = pd.DataFrame(
        [
            {"person_id": 112233, "measure_value": 10},
            {"person_id": 445566, "measure_value": 20},
        ],
        columns=["person_id", "measure_value"],
    )
    variants = Counter({112233: 1})
    joined = PhenoTool.join_pheno_df_with_variants(pheno_df, variants)
    expected = pd.DataFrame(
        [
            {"person_id": 112233, "measure_value": 10, "variant_count": 1.0},
            {"person_id": 445566, "measure_value": 20, "variant_count": 0.0},
        ],
        columns=["person_id", "measure_value", "variant_count"],
    )
    assert pd.DataFrame.equals(joined, expected)


def test_join_pheno_df_with_variants_non_counter_variants() -> None:
    with pytest.raises(AssertionError):
        PhenoTool.join_pheno_df_with_variants(
            pd.DataFrame(columns=["person_id"]), None,  # type: ignore
        )
    with pytest.raises(AssertionError):
        PhenoTool.join_pheno_df_with_variants(
            pd.DataFrame(columns=["person_id"]), {},  # type: ignore
        )
    with pytest.raises(AssertionError):
        PhenoTool.join_pheno_df_with_variants(
            pd.DataFrame(columns=["person_id"]), set(),  # type: ignore
        )


def test_join_pheno_df_with_empty_pheno_df() -> None:
    pheno_df = pd.DataFrame([], columns=["person_id", "measure_value"])
    variants = Counter({112233: 1})
    with pytest.raises(AssertionError):
        PhenoTool.join_pheno_df_with_variants(pheno_df, variants)


def test_normalize_df() -> None:
    pheno_df = pd.DataFrame(
        [
            {"person_id": 112233, "i1.m1": 1e6, "i1.m2": 1e3},
            {"person_id": 445566, "i1.m1": 2e12, "i1.m2": 1e-3},
        ],
        columns=["person_id", "i1.m1", "i1.m2"],
    )

    normalized = PhenoTool._normalize_df(
        pheno_df, "i1.m1", normalize_by=["i1.m2"],
    )

    assert list(normalized) == ["person_id", "i1.m1", "i1.m2", "normalized"]
    assert normalized["person_id"][0] == pytest.approx(112233)
    assert normalized["person_id"][1] == pytest.approx(445566)
    assert normalized["i1.m1"][0] == pytest.approx(1e6)
    assert normalized["i1.m1"][1] == pytest.approx(2e12)
    assert normalized["i1.m2"][0] == pytest.approx(1e3)
    assert normalized["i1.m2"][1] == pytest.approx(1e-3)
    assert normalized["normalized"][0] == pytest.approx(
        0.0004882, abs=1e-4,
    )
    assert normalized["normalized"][1] == pytest.approx(
        0.000488, abs=1e-2,
    )


def test_normalize_df_no_normalize_by() -> None:
    pheno_df = pd.DataFrame(
        [
            {"person_id": 112233, "i1.m1": 10},
            {"person_id": 445566, "i1.m1": 20},
        ],
        columns=["person_id", "i1.m1"],
    )
    expected = pd.DataFrame(
        [
            {"person_id": 112233, "i1.m1": 10, "normalized": 10},
            {"person_id": 445566, "i1.m1": 20, "normalized": 20},
        ],
        columns=["person_id", "i1.m1", "normalized"],
    )
    normalized = PhenoTool._normalize_df(pheno_df, "i1.m1")
    assert pd.DataFrame.equals(normalized, expected)


def test_normalize_df_does_not_contain_measure_id() -> None:
    pheno_df = pd.DataFrame(
        [
            {"person_id": 112233, "i1.m2": 1e6, "i1.m3": 1e3},
            {"person_id": 445566, "i1.m2": 2e12, "i1.m3": 1e-3},
        ],
        columns=["person_id", "i1.m2", "i1.m3"],
    )

    with pytest.raises(AssertionError):
        PhenoTool._normalize_df(pheno_df, "i1.m1", normalize_by=["i1.m2"])


def test_normalize_df_does_not_contain_normalize_measure_id() -> None:
    pheno_df = pd.DataFrame(
        [
            {"person_id": 112233, "i1.m1": 1e6, "i1.m2": 1e3},
            {"person_id": 445566, "i1.m1": 2e12, "i1.m2": 1e-3},
        ],
        columns=["person_id", "i1.m1", "i1.m2"],
    )

    with pytest.raises(AssertionError):
        PhenoTool._normalize_df(pheno_df, "i1.m1", normalize_by=["i1.m3"])


def test_calc_base_stats() -> None:
    count, mean, std = PhenoTool._calc_base_stats(
        np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]))
    assert count == 9
    assert mean == 5
    assert std == pytest.approx(1.686899413014786, abs=1e-15)


def test_calc_base_stats_empty_arr() -> None:
    count, mean, std = PhenoTool._calc_base_stats(np.array([]))
    assert count == 0
    assert mean == 0.0
    assert std == 0.0


def test_calc_pv() -> None:
    res = PhenoTool._calc_pv(
        np.array([1, 2, 3]), np.array([0, 1, 2]))
    assert res == pytest.approx(0.2878641347266908, abs=1e-16)


@pytest.mark.parametrize(
    "positive,negative", [([1], [1, 1]), ([1, 1], [1]), ([1], [1])],
)
def test_calc_pv_less_than_2(positive: list[int], negative: list[int]) -> None:
    assert PhenoTool._calc_pv(positive, negative) == "NA"  # type: ignore


def test_calc_stats(mocker: pytest_mock.MockerFixture) -> None:
    data = pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4", "5"],
            "sex": [Sex.M, Sex.F, Sex.M, Sex.F, Sex.M],
            "normalized": [0.1, 0.2, 0.3, 0.4, 0.5],
            "variant_count": [1, 1, 0, 0, 1],
        },
    )

    mocker.spy(PhenoTool, "_calc_pv")

    res = PhenoTool._calc_stats(data, None)
    assert isinstance(res, PhenoResult)

    PhenoTool._calc_pv.assert_called_once()  # type: ignore
    positive, negative = \
        PhenoTool._calc_pv.call_args_list[0][0]  # type: ignore
    assert list(positive) == [0.1, 0.2, 0.5]
    assert list(negative) == [0.3, 0.4]


def test_calc_stats_split_by_sex_male(
    mocker: pytest_mock.MockerFixture,
) -> None:
    data = pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4", "5"],
            "sex": [Sex.M, Sex.F, Sex.M, Sex.F, Sex.M],
            "normalized": [0.1, 0.2, 0.3, 0.4, 0.5],
            "variant_count": [1, 1, 0, 0, 1],
        },
    )

    mocker.spy(PhenoTool, "_calc_pv")

    res = PhenoTool._calc_stats(data, Sex.M)
    assert isinstance(res, PhenoResult)

    PhenoTool._calc_pv.assert_called_once()  # type: ignore
    positive, negative = \
        PhenoTool._calc_pv.call_args_list[0][0]  # type: ignore
    assert list(positive) == [0.1, 0.5]
    assert list(negative) == [0.3]


def test_calc_stats_split_by_sex_female(
    mocker: pytest_mock.MockerFixture,
) -> None:
    data = pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4", "5"],
            "sex": [Sex.M, Sex.F, Sex.M, Sex.F, Sex.M],
            "normalized": [0.1, 0.2, 0.3, 0.4, 0.5],
            "variant_count": [1, 1, 0, 0, 1],
        },
    )

    mocker.spy(PhenoTool, "_calc_pv")

    res = PhenoTool._calc_stats(data, Sex.F)
    assert isinstance(res, PhenoResult)

    PhenoTool._calc_pv.assert_called_once()  # type: ignore
    positive, negative = \
        PhenoTool._calc_pv.call_args_list[0][0]  # type: ignore
    assert list(positive) == [0.2]
    assert list(negative) == [0.4]


def test_calc_stats_empty_data() -> None:
    result = PhenoTool._calc_stats(pd.DataFrame([]), None)
    assert isinstance(result, PhenoResult)
    assert result.positive_count == 0
    assert result.positive_mean == 0
    assert result.positive_deviation == 0
    assert result.negative_count == 0
    assert result.negative_mean == 0
    assert result.negative_deviation == 0
    assert result.pvalue == "NA"  # type: ignore


def test_calc(
    mocker: pytest_mock.MockerFixture,
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    variants = Counter(
        {
            "f4.p1": 1,
            "f5.p1": 1,
            "f7.p1": 1,
            "f10.p1": 1,
            "f12.p1": 1,
            "f16.p1": 1,
            "f24.p1": 1,
            "f25.p1": 1,
            "f30.p1": 1,
            "f32.p1": 1,
        },
    )
    pheno_df = pheno_tool.create_df("i1.m1")
    merged_df = PhenoTool.join_pheno_df_with_variants(
        pheno_df, variants,
    )

    mocker.spy(PhenoTool, "join_pheno_df_with_variants")
    mocker.spy(pheno_tool, "_calc_stats")

    pheno_tool.calc("i1.m1", variants, sex_split=False)

    pheno_tool._calc_stats.assert_called_once()  # type: ignore
    PhenoTool.join_pheno_df_with_variants.assert_called_once()  # type: ignore

    call_arg_df, call_arg_sex_split = \
        pheno_tool._calc_stats.call_args_list[0][0]  # type: ignore
    assert merged_df.equals(call_arg_df)
    assert call_arg_sex_split is None


def test_calc_split_by_sex(
    mocker: pytest_mock.MockerFixture,
    t4c8_study_1_pheno: PhenotypeStudy,
) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    variants = Counter(
        {
            "f4.p1": 1,
            "f5.p1": 1,
            "f7.p1": 1,
            "f10.p1": 1,
            "f12.p1": 1,
            "f16.p1": 1,
            "f24.p1": 1,
            "f25.p1": 1,
            "f30.p1": 1,
            "f32.p1": 1,
        },
    )
    pheno_df = pheno_tool.create_df("i1.m1")
    merged_df = PhenoTool.join_pheno_df_with_variants(
        pheno_df, variants,
    )

    mocker.spy(PhenoTool, "join_pheno_df_with_variants")
    mocker.spy(pheno_tool, "_calc_stats")

    pheno_tool.calc("i1.m1", variants, sex_split=True)

    assert pheno_tool._calc_stats.call_count == 2  # type: ignore
    assert PhenoTool\
        .join_pheno_df_with_variants.call_count == 1  # type: ignore

    call_arg_df, call_arg_sex_split = \
        pheno_tool._calc_stats.call_args_list[0][0]  # type: ignore
    assert merged_df.equals(call_arg_df)
    assert call_arg_sex_split is Sex.M

    call_arg_df, call_arg_sex_split = \
        pheno_tool._calc_stats.call_args_list[1][0]  # type: ignore
    assert merged_df.equals(call_arg_df)
    assert call_arg_sex_split is Sex.F


def test_calc_empty_pheno_df(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    variants = Counter(
        {
            "f4.p1": 1,
            "f5.p1": 1,
            "f7.p1": 1,
            "f10.p1": 1,
            "f12.p1": 1,
            "f16.p1": 1,
            "f24.p1": 1,
            "f25.p1": 1,
            "f30.p1": 1,
            "f32.p1": 1,
        },
    )

    res = pheno_tool.calc("i1.m1", variants, person_ids=[])
    assert isinstance(res, PhenoResult)
    assert res.positive_count == 0
    assert res.positive_mean == 0
    assert res.positive_deviation == 0
    assert res.negative_count == 0
    assert res.negative_mean == 0
    assert res.negative_deviation == 0
    assert res.pvalue == "NA"  # type: ignore

    # pylint: disable=unbalanced-dict-unpacking
    res_m, res_f = \
        pheno_tool.calc(
            "i1.m1", variants, sex_split=True, person_ids=[],
        ).values()  # type: ignore
    assert isinstance(res_m, PhenoResult)
    assert isinstance(res_f, PhenoResult)

    assert res_m.positive_count == 0
    assert res_m.positive_mean == 0
    assert res_m.positive_deviation == 0
    assert res_m.negative_count == 0
    assert res_m.negative_mean == 0
    assert res_m.negative_deviation == 0
    assert res_m.pvalue == "NA"  # type: ignore

    assert res_f.positive_count == 0
    assert res_f.positive_mean == 0
    assert res_f.positive_deviation == 0
    assert res_f.negative_count == 0
    assert res_f.negative_mean == 0
    assert res_f.negative_deviation == 0
    assert res_f.pvalue == "NA"  # type: ignore


def test_calc_empty_variants(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(t4c8_study_1_pheno)
    variants: Counter = Counter()

    pheno_df = pheno_tool.create_df("i1.m1")
    res = pheno_tool.calc("i1.m1", variants)
    assert isinstance(res, PhenoResult)
    assert res.positive_count == 0
    assert res.positive_mean == 0
    assert res.positive_deviation == 0
    assert res.negative_count == len(pheno_df)
    assert res.negative_mean
    assert res.negative_deviation
    assert res.pvalue == "NA"  # type: ignore

    # pylint: disable=unbalanced-dict-unpacking
    res_m, res_f = \
        pheno_tool.calc("i1.m1", variants, sex_split=True).values()  # type: ignore
    assert isinstance(res_m, PhenoResult)
    assert isinstance(res_f, PhenoResult)

    assert res_m.positive_count == 0
    assert res_m.positive_mean == 0
    assert res_m.positive_deviation == 0
    assert res_m.negative_count == res.negative_count - res_f.negative_count
    assert res_m.negative_mean == 0.0
    assert res_m.negative_deviation == 0.0
    assert res_m.pvalue == "NA"  # type: ignore

    assert res_f.positive_count == 0
    assert res_f.positive_mean == 0
    assert res_f.positive_deviation == 0
    assert res_f.negative_count == res.negative_count - res_m.negative_count
    assert res_f.negative_mean
    assert res_f.negative_deviation
    assert res_f.pvalue == "NA"  # type: ignore


def test_normalize_df_by_empty_df(t4c8_study_1_pheno: PhenotypeStudy) -> None:
    pheno_df = t4c8_study_1_pheno.get_people_measure_values_df(
        ["i1.m1", "i1.m2"], person_ids=[],
    )

    with pytest.raises(AssertionError):
        PhenoTool._normalize_df(pheno_df, "i1.m1", "i1.m2")  # type: ignore
