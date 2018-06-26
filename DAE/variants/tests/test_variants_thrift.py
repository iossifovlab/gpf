'''
Created on Jun 26, 2018

@author: lubo
'''
from __future__ import print_function

import pytest


@pytest.mark.parametrize("fixture_name,count", [
    # "fixtures/effects_trio_multi",
    # "fixtures/effects_trio",
    ("fixtures/inheritance_multi", 6),
    # "fixtures/trios2",
])
def test_variants_spark_create(variants_thrift, fixture_name, count):

    svars = variants_thrift(fixture_name)
    assert svars is not None

    vs = svars.query_variants()
    vs = list(vs)
    print(vs)
    assert len(vs) == count
