# pylint: disable=W0621,C0114,C0116,W0212,W0613
from collections import Counter
from typing import List, Optional

import pytest
import pytest_mock

import pandas as pd
import numpy as np

from dae.pheno_tool.tool import PhenoResult, PhenoTool
from dae.variants.attributes import Sex
from dae.pheno.pheno_data import PhenotypeStudy


def test_init_pheno_df(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(
        fake_phenotype_data,
        "i1.m1",
        normalize_by=[{"instrument_name": "i1", "measure_name": "m2"}],
    )
    assert pheno_tool.pheno_df is not None
    assert not pheno_tool.pheno_df.empty
    assert set(pheno_tool.pheno_df) == {
        "person_id",
        "family_id",
        "role",
        "status",
        "sex",
        "i1.m1",
        "i1.m2",
        "normalized",
    }


def test_init_empty_person_ids(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1", person_ids=[])
    assert pheno_tool


def test_init_empty_person_ids_normalize(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(
        fake_phenotype_data,
        "i1.m1",
        person_ids=[],
        normalize_by=[{"instrument_name": "i1", "measure_name": "m2"}],
    )
    assert pheno_tool


def test_init_nonexistent_measure(fake_phenotype_data: PhenotypeStudy) -> None:
    with pytest.raises(AssertionError):
        PhenoTool(fake_phenotype_data, "i1.??")


def test_init_non_continuous_or_ordinal_measure(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    with pytest.raises(AssertionError):
        PhenoTool(fake_phenotype_data, "i1.m5")  # categorical
    with pytest.raises(AssertionError):
        PhenoTool(fake_phenotype_data, "i1.m9")  # raw


def test_init_with_person_ids(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(
        fake_phenotype_data,
        "i1.m1",
        person_ids=["f1.p1", "f3.p1", "f5.p1", "f7.p1"],
    )

    assert set(pheno_tool.pheno_df["person_id"]) == set(
        ["f1.p1", "f3.p1", "f5.p1", "f7.p1"]
    )


def test_init_normalize_measures(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    norm_measures_in = [
        {"measure_name": "??", "instrument_name": ""},
        {"measure_name": "m3", "instrument_name": ""},
        {"measure_name": "m7", "instrument_name": "i1"},
    ]

    norm_measures = pheno_tool._init_normalize_measures(norm_measures_in)
    assert len(norm_measures) == 2
    assert set(norm_measures) == {"i1.m3", "i1.m7"}
    for measure_id in norm_measures:
        assert fake_phenotype_data.has_measure(measure_id)


@pytest.mark.parametrize("measure_name", [("m4"), ("m5"), ("m6")])
def test_init_normalize_measures_non_continuous(
    fake_phenotype_data: PhenotypeStudy, measure_name: str
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    norm_measures = [
        {"measure_name": "??", "instrument_name": ""},
        {"measure_name": "m5", "instrument_name": ""},
        {"measure_name": "m7", "instrument_name": "i1"},
    ]
    with pytest.raises(AssertionError):
        pheno_tool._init_normalize_measures(norm_measures)


def test_get_normalize_measure_id_non_dict_measure(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    with pytest.raises(AssertionError):
        pheno_tool._get_normalize_measure_id(["measure"])  # type: ignore
    with pytest.raises(AssertionError):
        pheno_tool._get_normalize_measure_id("measure")  # type: ignore
    with pytest.raises(AssertionError):
        pheno_tool._get_normalize_measure_id(None)  # type: ignore


def test_get_normalize_measure_id_measure_dict_no_keys(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    with pytest.raises(AssertionError):
        pheno_tool._get_normalize_measure_id({"measure_name": "something"})
    with pytest.raises(AssertionError):
        pheno_tool._get_normalize_measure_id({"instrument_name": "something"})


def test_get_normalize_measure_id_no_instrument_name(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    measure_id = pheno_tool._get_normalize_measure_id(
        {"measure_name": "m3", "instrument_name": None}  # type: ignore
    )
    assert measure_id == "i1.m3"


def test_get_normalize_measure_id_with_instrument_name(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    measure_id = pheno_tool._get_normalize_measure_id(
        {"measure_name": "m7", "instrument_name": "i1"}
    )
    assert measure_id == "i1.m7"


def test_get_normalize_measure_id_same_measure(
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    measure_id = pheno_tool._get_normalize_measure_id(
        {"measure_name": "m1", "instrument_name": "i1"}
    )
    assert measure_id is None


@pytest.mark.parametrize(
    "measure_name,instrument_name",
    [("??", "i1"), ("i1", "??"), ("??", "??"), ("??", None)],
)
def test_get_normalize_measure_id_non_existent(
    fake_phenotype_data: PhenotypeStudy,
    measure_name: str,
    instrument_name: Optional[str]
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    measure_id = pheno_tool._get_normalize_measure_id(
        {"measure_name": measure_name,
         "instrument_name": instrument_name}  # type: ignore
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
            pd.DataFrame(columns=["person_id"]), None  # type: ignore
        )
    with pytest.raises(AssertionError):
        PhenoTool.join_pheno_df_with_variants(
            pd.DataFrame(columns=["person_id"]), {}  # type: ignore
        )
    with pytest.raises(AssertionError):
        PhenoTool.join_pheno_df_with_variants(
            pd.DataFrame(columns=["person_id"]), set()  # type: ignore
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
        pheno_df, "i1.m1", normalize_by=["i1.m2"]
    )

    assert list(normalized) == ["person_id", "i1.m1", "i1.m2", "normalized"]
    assert normalized["person_id"][0] == pytest.approx(112233)
    assert normalized["person_id"][1] == pytest.approx(445566)
    assert normalized["i1.m1"][0] == pytest.approx(1e6)
    assert normalized["i1.m1"][1] == pytest.approx(2e12)
    assert normalized["i1.m2"][0] == pytest.approx(1e3)
    assert normalized["i1.m2"][1] == pytest.approx(1e-3)
    assert normalized["normalized"][0] == pytest.approx(
        0.0004882, abs=1e-4
    )  # FIXME:
    assert normalized["normalized"][1] == pytest.approx(
        0.000488, abs=1e-2
    )  # FIXME:


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
    "positive,negative", [([1], [1, 1]), ([1, 1], [1]), ([1], [1])]
)
def test_calc_pv_less_than_2(positive: List[int], negative: List[int]) -> None:
    assert PhenoTool._calc_pv(positive, negative) == "NA"  # type: ignore


def test_calc_stats(mocker: pytest_mock.MockerFixture) -> None:
    data = pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4", "5"],
            "sex": [Sex.M, Sex.F, Sex.M, Sex.F, Sex.M],
            "normalized": [0.1, 0.2, 0.3, 0.4, 0.5],
            "variant_count": [1, 1, 0, 0, 1],
        }
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
    mocker: pytest_mock.MockerFixture
) -> None:
    data = pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4", "5"],
            "sex": [Sex.M, Sex.F, Sex.M, Sex.F, Sex.M],
            "normalized": [0.1, 0.2, 0.3, 0.4, 0.5],
            "variant_count": [1, 1, 0, 0, 1],
        }
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
    mocker: pytest_mock.MockerFixture
) -> None:
    data = pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4", "5"],
            "sex": [Sex.M, Sex.F, Sex.M, Sex.F, Sex.M],
            "normalized": [0.1, 0.2, 0.3, 0.4, 0.5],
            "variant_count": [1, 1, 0, 0, 1],
        }
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
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
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
        }
    )
    merged_df = PhenoTool.join_pheno_df_with_variants(
        pheno_tool.pheno_df, variants
    )

    mocker.spy(PhenoTool, "join_pheno_df_with_variants")
    mocker.spy(pheno_tool, "_calc_stats")

    pheno_tool.calc(variants, sex_split=False)

    pheno_tool._calc_stats.assert_called_once()  # type: ignore
    PhenoTool.join_pheno_df_with_variants.assert_called_once()  # type: ignore

    call_arg_df, call_arg_sex_split = \
        pheno_tool._calc_stats.call_args_list[0][0]  # type: ignore
    assert merged_df.equals(call_arg_df)
    assert call_arg_sex_split is None


def test_calc_split_by_sex(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy
) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
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
        }
    )
    merged_df = PhenoTool.join_pheno_df_with_variants(
        pheno_tool.pheno_df, variants
    )

    mocker.spy(PhenoTool, "join_pheno_df_with_variants")
    mocker.spy(pheno_tool, "_calc_stats")

    pheno_tool.calc(variants, sex_split=True)

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


def test_calc_empty_pheno_df(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1", person_ids=[])
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
        }
    )

    res = pheno_tool.calc(variants)
    assert isinstance(res, PhenoResult)
    assert res.positive_count == 0
    assert res.positive_mean == 0
    assert res.positive_deviation == 0
    assert res.negative_count == 0
    assert res.negative_mean == 0
    assert res.negative_deviation == 0
    assert res.pvalue == "NA"  # type: ignore

    res_m, res_f = \
        pheno_tool.calc(variants, sex_split=True).values()  # type: ignore
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


def test_calc_empty_variants(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_tool = PhenoTool(fake_phenotype_data, "i1.m1")
    variants: Counter = Counter()

    res = pheno_tool.calc(variants)
    assert isinstance(res, PhenoResult)
    assert res.positive_count == 0
    assert res.positive_mean == 0
    assert res.positive_deviation == 0
    assert res.negative_count == len(pheno_tool.pheno_df)
    assert res.negative_mean
    assert res.negative_deviation
    assert res.pvalue == "NA"  # type: ignore

    res_m, res_f = \
        pheno_tool.calc(variants, sex_split=True).values()  # type: ignore
    assert isinstance(res_m, PhenoResult)
    assert isinstance(res_f, PhenoResult)

    assert res_m.positive_count == 0
    assert res_m.positive_mean == 0
    assert res_m.positive_deviation == 0
    assert res_m.negative_count == res.negative_count - res_f.negative_count
    assert res_m.negative_mean
    assert res_m.negative_deviation
    assert res_m.pvalue == "NA"  # type: ignore

    assert res_f.positive_count == 0
    assert res_f.positive_mean == 0
    assert res_f.positive_deviation == 0
    assert res_f.negative_count == res.negative_count - res_m.negative_count
    assert res_f.negative_mean
    assert res_f.negative_deviation
    assert res_f.pvalue == "NA"  # type: ignore


def test_normalize_df_by_empty_df(fake_phenotype_data: PhenotypeStudy) -> None:
    pheno_df = fake_phenotype_data.get_persons_values_df(
        ["i1.m1", "i1.m2"], person_ids=[]
    )

    with pytest.raises(AssertionError):
        PhenoTool._normalize_df(pheno_df, "i1.m1", "i1.m2")  # type: ignore
