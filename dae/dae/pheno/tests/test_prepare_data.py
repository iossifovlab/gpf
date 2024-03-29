# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import os
from typing import Any, Optional

import pytest
import pytest_mock

import pandas as pd
import matplotlib.pyplot as plt

from dae.pheno.prepare_data import PreparePhenoBrowserBase
from dae.pheno.graphs import violinplot, stripplot, gender_palette

from dae.variants.attributes import Role, Sex
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
from dae.pheno.pheno_data import PhenotypeStudy


def test_augment_measure(
    fake_phenotype_data: PhenotypeStudy, output_dir: str
) -> None:
    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    df = prep._augment_measure_values_df(
        regressor, "test regression", regressand
    )
    assert df is not None

    roles = list(df["role"].unique())
    assert len(roles) == 3
    for role in [Role.parent, Role.sib, Role.prb]:
        assert role in roles
    assert list(df) == [
        "person_id",
        "family_id",
        "role",
        "status",
        "sex",
        "test regression",
        "i1.m1",
    ]
    assert len(df) > 0


def test_augment_measure_regressor_no_instrument_name(
    fake_phenotype_data: PhenotypeStudy, output_dir: str
) -> None:
    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    exp_df = prep._augment_measure_values_df(
        regressor, "test regression", regressand
    )
    assert exp_df is not None

    regressor.instrument_name = None
    df = prep._augment_measure_values_df(
        regressor, "test regression", regressand
    )
    assert df is not None

    assert list(df) == [
        "person_id",
        "family_id",
        "role",
        "status",
        "sex",
        "test regression",
        "i1.m1",
    ]
    assert len(df) > 0
    assert list(df["test regression"]) == list(exp_df["test regression"])


def test_augment_measure_with_identical_measures(
    fake_phenotype_data: PhenotypeStudy, output_dir: str
) -> None:
    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.age")
    regressor = fake_phenotype_data.get_measure("i1.age")
    df = prep._augment_measure_values_df(
        regressor, "test regression", regressand
    )
    assert df is None


def test_augment_measure_with_nonexistent_regressor(
    fake_phenotype_data: PhenotypeStudy, output_dir: str
) -> None:
    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i2.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    regressor.instrument_name = None
    df = prep._augment_measure_values_df(
        regressor, "test regression", regressand
    )
    assert df is None


def test_build_regression(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str
) -> None:

    fake_df = pd.DataFrame(
        {
            # Only two unique values, in order to test
            # the MIN_UNIQUE_VALUES check
            "i1.m1": [1, 2, 1, 2, 1, 2],
            "age": [1, 2, 3, 4, 5, 6],
            "role": [
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
            ],
            "sex": [
                Sex.male,
                Sex.female,
                Sex.male,
                Sex.female,
                Sex.male,
                Sex.female,
            ],
        }
    )

    def fake_augment_df(*args: Any) -> pd.DataFrame:
        return fake_df

    def fake_linregres(*args: Any) -> Any:

        class Result:  # pylint: disable=too-few-public-methods
            pvalues = [0.123456, 0.123456]

        res_male = Result()
        res_female = Result()
        res_female.pvalues[1] = 0.654321
        return (res_male, res_female)

    def fake_savefig(*args: Any) -> tuple[str, str]:
        return ("figsmall", "fig")

    mocked_linregres = mocker.patch(
        "dae.pheno.prepare_data.draw_linregres",
        side_effect=fake_linregres,
    )
    mocker.patch(
        "dae.pheno.prepare_data.PreparePhenoBrowserBase.save_fig",
        side_effect=fake_savefig,
    )
    mocker.patch(
        "dae.pheno.prepare_data."
        "PreparePhenoBrowserBase._augment_measure_values_df",
        side_effect=fake_augment_df,
    )

    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    jitter = 0.32403423849

    res = prep.build_regression(regressand, regressor, jitter)
    assert res is not None
    assert isinstance(res, dict)

    mocked_linregres.assert_called_once()
    _dfdf, col1, col2, jitter = mocked_linregres.call_args[0]
    assert col1 == "age"
    assert col2 == "i1.m1"
    assert jitter == 0.32403423849


def test_build_regression_min_vals(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str
) -> None:
    fake_df = pd.DataFrame(
        {
            "i1.m1": [1, 2, 3, 4, 5],
            "age": [1, 2, 3, 4, 5],
            "role": [Role.prb, Role.prb, Role.prb, Role.prb, Role.prb],
            "sex": [Sex.male, Sex.female, Sex.male, Sex.female, Sex.male],
        }
    )

    def fake_augment_df(*args: Any) -> pd.DataFrame:
        return fake_df

    mocker.patch(
        "dae.pheno.prepare_data."
        "PreparePhenoBrowserBase._augment_measure_values_df",
        side_effect=fake_augment_df,
    )

    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    jitter = 0.32403423849

    assert not prep.build_regression(regressand, regressor, jitter)


def test_build_regression_min_unique_vals(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str
) -> None:
    fake_df = pd.DataFrame(
        {
            "i1.m1": [1, 1, 1, 1, 1, 1],
            "age": [1, 2, 3, 4, 5, 6],
            "role": [
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
            ],
            "sex": [
                Sex.male,
                Sex.female,
                Sex.male,
                Sex.female,
                Sex.male,
                Sex.female,
            ],
        }
    )

    def fake_augment_df(*args: Any) -> pd.DataFrame:
        return fake_df

    mocker.patch(
        "dae.pheno.prepare_data."
        "PreparePhenoBrowserBase._augment_measure_values_df",
        side_effect=fake_augment_df,
    )

    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    jitter = 0.32403423849

    assert not prep.build_regression(regressand, regressor, jitter)


def test_build_regression_identical_measures(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str
) -> None:
    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.age")
    regressor = fake_phenotype_data.get_measure("i1.age")
    jitter = 0.32403423849

    assert not prep.build_regression(regressand, regressor, jitter)


def test_build_regression_aug_df_is_none(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str
) -> None:
    def fake_augment_df(*args: Any) -> Optional[pd.DataFrame]:
        return None

    mocker.patch(
        "dae.pheno.prepare_data."
        "PreparePhenoBrowserBase._augment_measure_values_df",
        side_effect=fake_augment_df,
    )

    prep = PreparePhenoBrowserBase("fake", fake_phenotype_data, output_dir)
    regressand = fake_phenotype_data.get_measure("i1.m1")
    regressor = fake_phenotype_data.get_measure("i1.age")
    jitter = 0.32403423849

    assert not prep.build_regression(regressand, regressor, jitter)


def test_handle_regressions(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str,
    fake_phenotype_data_config: str
) -> None:
    def fake_build_regression(
        dependent_measure: str, independent_measure: str, jitter: float
    ) -> dict:
        return {
            "regressand": dependent_measure,
            "regressor": independent_measure,
            "jitter": jitter,
            "pvalue_regression_male": 0,
            "pvalue_regression_female": 0,
        }

    mocked = mocker.patch(
        "dae.pheno.prepare_data."
        "PreparePhenoBrowserBase.build_regression",
        side_effect=fake_build_regression,
    )

    reg = GPFConfigParser.load_config(
        fake_phenotype_data_config, pheno_conf_schema
    )
    prep = PreparePhenoBrowserBase(
        "fake", fake_phenotype_data, output_dir, reg
    )
    regressand = fake_phenotype_data.get_measure("i1.m1")

    res = [r for r in prep.handle_regressions(regressand) if r is not None]
    assert len(res) == 2
    assert sorted([r["regression_id"] for r in res]) == sorted(["age", "nviq"])

    mocked.assert_called()
    measure, reg_measure, jitter = mocked.call_args_list[0][0]
    assert measure.measure_id == "i1.m1"
    assert reg_measure.measure_id == "i1.age"
    assert jitter == 0.12
    measure, reg_measure, jitter = mocked.call_args_list[1][0]
    assert measure.measure_id == "i1.m1"
    assert reg_measure.measure_id == "i1.iq"
    assert jitter == 0.13


def test_handle_regressions_non_continuous_or_ordinal_measure(
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str,
    fake_phenotype_data_config: str
) -> None:
    reg = GPFConfigParser.load_config(
        fake_phenotype_data_config, pheno_conf_schema
    )
    prep = PreparePhenoBrowserBase(
        "fake", fake_phenotype_data, output_dir, reg
    )
    regressand_categorical = fake_phenotype_data.get_measure("i1.m5")
    regressand_raw = fake_phenotype_data.get_measure("i1.m6")

    with pytest.raises(StopIteration):
        next(prep.handle_regressions(regressand_categorical))

    with pytest.raises(StopIteration):
        next(prep.handle_regressions(regressand_raw))


def test_handle_regressions_regressand_is_regressor(
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str,
    fake_phenotype_data_config: str
) -> None:
    reg = GPFConfigParser.load_config(
        fake_phenotype_data_config, pheno_conf_schema
    )
    prep = PreparePhenoBrowserBase(
        "fake", fake_phenotype_data, output_dir, reg
    )
    regressand = fake_phenotype_data.get_measure("i1.age")

    with pytest.raises(StopIteration):
        next(prep.handle_regressions(regressand))


def test_handle_regressions_default_jitter(
    mocker: pytest_mock.MockerFixture,
    fake_phenotype_data: PhenotypeStudy,
    output_dir: str,
    fake_phenotype_data_config: str
) -> None:
    def fake_build_regression(*args: Any) -> dict:
        return {"pvalue_regression_male": 0, "pvalue_regression_female": 0}

    mocked = mocker.patch(
        "dae.pheno.prepare_data."
        "PreparePhenoBrowserBase.build_regression",
        side_effect=fake_build_regression,
    )

    reg = GPFConfigParser.load_config(
        fake_phenotype_data_config, pheno_conf_schema
    )
    prep = PreparePhenoBrowserBase(
        "fake", fake_phenotype_data, output_dir, reg
    )
    regressand = fake_phenotype_data.get_measure("i1.m1")
    for _i in prep.handle_regressions(regressand):
        pass

    mocked.assert_called()
    _measure, _reg_measure, jitter = mocked.call_args_list[0][0]
    assert jitter == 0.12
    _measure, _reg_measure, jitter = mocked.call_args_list[1][0]
    assert jitter == 0.13


def test_draw_violinplot(
    fake_phenotype_data: PhenotypeStudy,
    temp_dirname_figures: str
) -> None:

    df = fake_phenotype_data.get_people_measure_values_df(["i1.m5", "i1.m6"])
    for i in range(len(df)):
        df["i1.m5"][i] = i
        df["i1.m6"][i] = i * 2

    violinplot(
        data=df,
        x="i1.m5",
        y="i1.m6",
        hue="sex",
        hue_order=[Sex.male, Sex.female],
        linewidth=1,
        split=True,
        scale="count",
        scale_hue=False,
        palette=gender_palette(),
        saturation=1,
    )

    plt.savefig(os.path.join(temp_dirname_figures, "violinplot"))


def test_draw_stripplot(
    fake_phenotype_data: PhenotypeStudy,
    temp_dirname_figures: str
) -> None:

    df = fake_phenotype_data.get_people_measure_values_df(["i1.m5", "i1.m6"])
    for i in range(len(df)):
        df["i1.m5"][i] = i
        df["i1.m6"][i] = i * 2

    stripplot(
        data=df,
        x="i1.m5",
        y="i1.m6",
        hue="sex",
        hue_order=[Sex.male, Sex.female],
        jitter=0.025,
        size=2,
        palette=gender_palette(),
        linewidth=0.1,
    )

    plt.savefig(os.path.join(temp_dirname_figures, "stripplot"))
