# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import numpy as np
from dae.pheno.utils.lin_regress import LinearRegression


def test_lin_regress() -> None:
    x = np.array([[1], [2], [3], [4], [5], [6], [7]])
    y = np.array([1.5, 3.8, 6.7, 9.0, 11.2, 13.6, 16])
    result = LinearRegression().calc_regression(x, y)

    expected = np.array([
        1.58571429,
        4.0,
        6.41428571,
        8.82857143,
        11.24285714,
        13.65714286,
        16.07142857,
    ])
    assert all(np.isclose(expected, result.predict(x)))
