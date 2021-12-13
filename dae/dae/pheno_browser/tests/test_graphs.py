import pytest
import pandas as pd
from dae.pheno_browser.graphs import draw_linregres
from dae.variants.attributes import Role, Sex


def test_linregres_notcorrelated():
    df = pd.DataFrame(
        {
            "i1.m1": [1, 1, 2, 2, 3, 3],
            "age": [1, 1, 1, 1, 1, 1],
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
    res_male, res_female = draw_linregres(df, "age", "i1.m1")
    expected_value = 7.41799e-2
    assert res_male is not None
    assert res_female is not None
    assert res_male.pvalues[1] == pytest.approx(expected_value)
    assert res_female.pvalues[1] == pytest.approx(expected_value)


def test_linregres_positive():
    df = pd.DataFrame(
        {
            "i1.m1": [1, 1, 2, 2, 3, 3],
            "age": [1, 1, 2, 2, 3, 3],
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
    res_male, res_female = draw_linregres(df, "age", "i1.m1")
    expected_value = 1.18e-15
    assert res_male is not None
    assert res_female is not None
    assert res_male.pvalues[1] == pytest.approx(expected_value)
    assert res_female.pvalues[1] == pytest.approx(expected_value)


def test_linregres_negative():
    df = pd.DataFrame(
        {
            "i1.m1": [1, 1, 2, 2, 3, 3],
            "age": [3, 3, 2, 2, 1, 1],
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
    res_male, res_female = draw_linregres(df, "age", "i1.m1")
    expected_value = 6.92e-16
    assert res_male is not None
    assert res_female is not None
    assert res_male.pvalues[1] == pytest.approx(expected_value)
    assert res_female.pvalues[1] == pytest.approx(expected_value)


def test_linregres_m1_male():
    df = pd.DataFrame(
        {
            "i1.m1": [
                166.33975,
                111.538,
                68.00149,
                157.61835,
                171.89038,
                143.50627,
                190.44301,
                129.93854,
                146.61195,
                109.791084,
                187.06744,
                98.911674,
                169.9289,
                115.063866,
                97.23721,
                158.89444,
                120.092896,
                110.66704,
                147.52153,
                147.41417,
                109.65686,
                177.16641,
                108.904106,
                87.50109,
                185.5127,
                170.75998,
                179.97546,
                179.14534,
                187.90378,
                203.8139,
                107.01703,
                110.25811,
                163.88484,
                195.29074
            ],
            "age": [
                110.71113119,
                75.83138675,
                96.63452028,
                99.5488491,
                80.17124991,
                66.97818515,
                70.01276006,
                78.45678149,
                51.92404741,
                55.53042886,
                104.22668451,
                87.08972873,
                72.26109161,
                60.9857896,
                101.59533297,
                59.1819379,
                52.28330864,
                64.92778794,
                95.95975775,
                93.69436739,
                71.33388383,
                91.82305943,
                69.33834058,
                73.96827354,
                46.36919772,
                114.5881324,
                96.3399881,
                50.02575802,
                81.79714976,
                81.62160052,
                92.61160024,
                69.54791318,
                99.95576118,
                35.19528659
            ],
            "role": [
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
            ],
            "sex": [
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
                Sex.male,
            ],
        }
    )

    res_male, res_female = draw_linregres(df, "age", "i1.m1")
    expected_value = 9.71129360e-01
    assert res_male is not None
    assert res_female is None
    assert res_male.pvalues[1] == pytest.approx(expected_value)


def test_linregres_m1_female():
    df = pd.DataFrame(
        {
            "i1.m1": [
                189.63339,
                106.0046,
                126.78941,
                114.90047,
                121.42031
            ],
            "age": [
                110.4315545,
                58.88671455,
                90.00139293,
                72.69365265,
                114.74254639
            ],
            "role": [
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
                Role.prb,
            ],
            "sex": [
                Sex.female,
                Sex.female,
                Sex.female,
                Sex.female,
                Sex.female,
            ],
        }
    )

    res_male, res_female = draw_linregres(df, "age", "i1.m1")
    expected_value = 0.25117455
    assert res_male is None
    assert res_female is not None
    assert res_female.pvalues[1] == pytest.approx(expected_value)
