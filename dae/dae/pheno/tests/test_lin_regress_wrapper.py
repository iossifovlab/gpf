import numpy as np
from dae.pheno.utils.lin_regress_wrapper import LinearRegressionWrapper


def test_lin_regress_wrapper():
    x = [1, 2, 3, 4, 5, 6, 7]
    y = [1.5, 3.8, 6.7, 9.0, 11.2, 13.6, 16]
    result = LinearRegressionWrapper(x, y)

    expected = np.array([
        1.58571429,
        4.0,
        6.41428571,
        8.82857143,
        11.24285714,
        13.65714286,
        16.07142857
    ])
    assert all(np.isclose(expected, result.predict()))

    expected = np.array([
        -0.08571429,
        -0.2,
        0.28571429,
        0.17142857,
        -0.04285714,
        -0.05714286,
        -0.07142857
    ])
    assert all(np.isclose(expected, result.resid()))
