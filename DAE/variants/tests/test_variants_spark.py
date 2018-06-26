'''
Created on Jun 26, 2018

@author: lubo
'''
import pytest


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio",
    "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_variants_spark_create(variants_spark, fixture_name):

    svars = variants_spark(fixture_name)
    assert svars is not None
