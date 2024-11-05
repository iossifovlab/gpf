# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np
import pytest

from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize("mat,expected", [
    (
        np.array([[0, 0, 0], [0, 1, 0]], dtype=np.int8),
        "000/010",
    ),
    (
        [[0, 0, 0], [0, 1, 0]],
        "000/010",
    ),
    (
        np.array([[2, 2, 1], [0, 0, 0], [0, 0, 1]], dtype=np.int8),
        "221/000/001",
    ),
    (
        [[2, 2, 1], [0, 0, 0], [0, 0, 1]],
        "221/000/001",
    ),
])
def test_mat2str(
    mat: np.ndarray | list[list[int]],
    expected: str,
) -> None:
    res = mat2str(mat)

    assert res == expected


@pytest.mark.parametrize("col_sep,row_sep,expected", [
    (
        "", "/",
        "221/000/001",
    ),
    (
        " ", "/",
        "2 2 1/0 0 0/0 0 1",
    ),
    (
        ",", "/",
        "2,2,1/0,0,0/0,0,1",
    ),
    (
        ",", ";",
        "2,2,1;0,0,0;0,0,1",
    ),
])
def test_mat2str_col_row_sep(
    col_sep: str,
    row_sep: str,
    expected: str,
) -> None:
    res = mat2str(
        [[2, 2, 1], [0, 0, 0], [0, 0, 1]],
        col_sep=col_sep,
        row_sep=row_sep,
    )

    assert res == expected
