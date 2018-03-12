'''
Created on Mar 7, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

import numpy as np


def assert_annotation_equals(vars_df, vars1_df):

    for v1, v2 in zip(vars_df.to_dict(orient='record'),
                      vars1_df.to_dict(orient='record')):
        for k in v1.keys():
            res = v1[k] == v2[k]
            if isinstance(res, np.ndarray):
                # print(k, v1[k], v2[k], type(v1[k]), type(v2[k]),
                #       v1[k].dtype.type, v2[k].dtype.type,
                #       v1[k].dtype, v2[k].dtype)

                if v1[k].dtype.type is np.string_ or \
                        v1[k].dtype.type is np.unicode_:
                    assert np.all(res)
                else:
                    assert np.allclose(v1[k], v2[k], rtol=1e-5)
            elif isinstance(v1[k], float):
                assert v1[k] == pytest.approx(v2[k], 1e-6)
            else:
                assert v1[k] == v2[k]
