"""
Created on Mar 7, 2018

@author: lubo
"""
import pytest

import numpy as np
import os


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def assert_annotation_equals(vars_df, vars1_df):

    for v1, v2 in zip(
        vars_df.to_dict(orient="record"), vars1_df.to_dict(orient="record")
    ):
        for k in list(v1.keys()):
            res = v1[k] == v2[k]
            print(
                k,
                "|{}|".format(v1[k]),
                "|{}|".format(v2[k]),
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
                        "objects: {}: {} == {} ({}, {})".format(
                            k, v1[k], v2[k], type(v1[k]), type(v2[k])
                        )
                    )
                    assert all(v1[k] == v2[k])
                else:
                    print(
                        "{}: {} == {} ({}, {})".format(
                            k, v1[k], v2[k], type(v1[k]), type(v2[k])
                        )
                    )
                    assert np.allclose(v1[k], v2[k], rtol=1e-3)
            elif isinstance(v1[k], float):
                assert v1[k] == pytest.approx(
                    v2[k], rel=1e-5
                ), "{}: {} == {} ({}, {})".format(
                    k, v1[k], v2[k], type(v1[k]), type(v2[k])
                )
            else:
                assert v1[k] == v2[k], "{}: {} == {} ({}, {})".format(
                    k, v1[k], v2[k], type(v1[k]), type(v2[k])
                )
