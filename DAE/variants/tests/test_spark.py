'''
Created on Jun 12, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
import pytest
import os

from impala.util import as_pandas


def test_start_stop_thriftserver(testing_thriftserver):
    print("testing_thriftserver:", testing_thriftserver)
    assert testing_thriftserver is not None


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

    pedigree_filename, summary_filename, allele_filename = \
        parquet_variants(fixture_name)
    print(pedigree_filename, summary_filename, allele_filename)

    assert os.path.exists(pedigree_filename)
    assert os.path.exists(summary_filename)
    assert os.path.exists(allele_filename)


@pytest.mark.parametrize("fixture_name, count", [
    ("fixtures/effects_trio_multi", 9),
    ("fixtures/effects_trio", 23),
    ("fixtures/inheritance_multi", 12),
    ("fixtures/trios2", 76),
])
def test_parquet_select(
        testing_thriftserver, parquet_variants, fixture_name, count):
    assert testing_thriftserver is not None

    pedigree_filename, summary_filename, allele_filename = \
        parquet_variants(fixture_name)
    print(pedigree_filename, summary_filename, allele_filename)

    q = """
    SELECT * FROM parquet.`file://{}` AS A
    INNER JOIN parquet.`file://{}` AS B
    ON A.summary_variant_index = B.summary_variant_index
    """.format(allele_filename, summary_filename)
    print(q)

    cursor = testing_thriftserver.cursor()
    cursor.execute(q)
    df = as_pandas(cursor)
    print("variants:", len(df))
    # assert len(df) == count
