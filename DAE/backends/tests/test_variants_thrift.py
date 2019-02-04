'''
Created on Jun 26, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest


@pytest.mark.parametrize("fixture_name,count", [
    # "fixtures/effects_trio_multi",
    ("fixtures/effects_trio", 10),
    ("fixtures/inheritance_multi", 6),
    # "fixtures/trios2",
])
def test_variants_spark_create(variants_thrift, fixture_name, count):

    svars = variants_thrift(fixture_name)
    assert svars is not None

    vs = svars.query_variants(return_reference=True)
    vs = list(vs)
    print(vs)
    assert len(vs) == count


@pytest.mark.parametrize("variants", [
    # "variants_df",
    "variants_thrift",
])
@pytest.mark.parametrize("fixture_name,count", [
    ("fixtures/effects_trio_multi", 3),
])
def test_variants_effects_trio_multi(
        variants_impl, variants, fixture_name, count):

    svars = variants_impl(variants)(fixture_name)
    assert svars is not None

    vs = svars.query_variants()
    vs = list(vs)
    print(vs)
    assert len(vs) == count
