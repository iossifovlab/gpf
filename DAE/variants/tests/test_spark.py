'''
Created on Jun 12, 2018

@author: lubo
'''
from __future__ import print_function
import pytest
import os

from impala.util import as_pandas


@pytest.mark.spark
def test_start_stop_thriftserver(testing_thriftserver):
    print("testing_thriftserver:", testing_thriftserver)
    assert testing_thriftserver is not None


@pytest.mark.spark
def test_start_stop_thriftserver2(testing_thriftserver):
    print("testing_thriftserver:", testing_thriftserver)
    assert testing_thriftserver is not None


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio",
    "fixtures/inheritance_multi",
    "fixtures/trios2",
])
def test_parquet_variants(
        parquet_variants, fixture_name):

    summary_filename, family_filename = parquet_variants(fixture_name)
    print(summary_filename, family_filename)

    assert os.path.exists(summary_filename)
    assert os.path.exists(family_filename)


@pytest.mark.spark
@pytest.mark.parametrize("fixture_name, count", [
    ("fixtures/effects_trio_multi", 12),
    ("fixtures/effects_trio", 13),
    ("fixtures/inheritance_multi", 6),
    ("fixtures/trios2", 56),
])
def test_parquet_select(
        testing_thriftserver, parquet_variants, fixture_name, count):
    assert testing_thriftserver is not None

    summary_filename, family_filename = parquet_variants(fixture_name)
    print(summary_filename, family_filename)

    q = """
    SELECT * FROM parquet.`file://{}` AS A
    INNER JOIN parquet.`file://{}` AS B
    ON A.var_index = B.var_index
    """.format(family_filename, summary_filename)
    print(q)

    cursor = testing_thriftserver.cursor()
    cursor.execute(q)
    df = as_pandas(cursor)
    print("variants:", len(df))
    assert len(df) == count
