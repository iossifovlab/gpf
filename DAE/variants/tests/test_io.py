'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function

# import os

import pytest

# import pyarrow.parquet as pq
# import dask.dataframe as dd

from variants.loader import RawVariantsLoader
from variants.tests.common_tests_helpers import assert_annotation_equals


from variants.parquet_io import \
    summary_parquet_schema_flat, summary_table, save_summary_to_parquet,\
    read_summary_from_parquet
# from variants.attributes import Inheritance


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio",
])
def test_annotation_parquet(variants_vcf, fixture_name, temp_filename):
    schema = summary_parquet_schema_flat()
    print(schema)
    print(dir(schema))
    print(schema.names)
    for name in schema.names:
        print(schema.field_by_name(name))
        print(schema.get_field_index(name))

    fvars = variants_vcf(fixture_name)
    annot_df = fvars.annot_df
    table = summary_table(annot_df)
    assert table is not None
    print(dir(table))

    df = table.to_pandas()
    print(df.head())

    save_summary_to_parquet(df, temp_filename)

    df1 = read_summary_from_parquet(temp_filename)
    assert df1 is not None
    print(df1.head())

    assert_annotation_equals(df, df1)


@pytest.mark.parametrize("fixture_name,storage", [
    ("fixtures/effects_trio_multi", "csv"),
    ("fixtures/effects_trio_multi", "parquet"),
    ("fixtures/effects_trio", "csv"),
    ("fixtures/effects_trio", "parquet"),
])
def test_serialize_deserialize(
        fixture_name, variants_vcf, storage, temp_filename):

    fvars = variants_vcf(fixture_name)

    assert fvars.annot_df is not None

    outfile = temp_filename
    # outfile = "annot.tmp"

    RawVariantsLoader.save_annotation_file(
        fvars.annot_df, outfile, storage=storage)
    annot_df = RawVariantsLoader.load_annotation_file(
        outfile, storage=storage)
    assert annot_df is not None

    assert_annotation_equals(annot_df, fvars.annot_df)
