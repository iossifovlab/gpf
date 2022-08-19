# pylint: disable=W0621,C0114,C0116,W0212,W0613,invalid-name
import os
import numpy as np

import pytest


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def assert_annotation_equals(vars_df, vars1_df):

    for v1, v2 in zip(
        vars_df.to_dict(orient="records"), vars1_df.to_dict(orient="records")
    ):
        for k in list(v1.keys()):
            res = v1[k] == v2[k]
            print(
                k,
                f"|{v1[k]}|".format(),
                f"|{v2[k]}|".format(),
                type(v1[k]),
                type(v2[k]),
            )
            print(vars_df[k].values)
            print(vars1_df[k].values)

            if isinstance(res, np.ndarray):
                if (
                    isinstance(v1[k], str)
                    or v1[k].dtype.type is np.string_
                    or v1[k].dtype.type is np.unicode_
                ):
                    assert np.all(res)
                elif v1[k].dtype.type == np.object_:
                    print(
                        f"objects: {k}: {v1[k]} == {v2[k]} "
                        f"({type(v1[k])}, {type(v2[k])})"
                    )
                    assert all(v1[k] == v2[k])
                else:
                    print(
                        f"{k}: {v1[k]} == {v2[k]} "
                        f"({type(v1[k])}, {type(v2[k])})"
                    )
                    assert np.allclose(v1[k], v2[k], rtol=1e-3)
            elif isinstance(v1[k], float):
                assert v1[k] == pytest.approx(
                    v2[k], rel=1e-5
                ), f"{k}: {v1[k]} == {v2[k]} ({type(v1[k])}, {type(v2[k])})"
            else:
                assert v1[k] == v2[k], \
                    f"{k}: {v1[k]} == {v2[k]} ({type(v1[k])}, {type(v2[k])})"
