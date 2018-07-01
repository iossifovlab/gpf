'''
Created on Mar 7, 2018

@author: lubo
'''
# import pandas as pd
# import pyarrow as pa
#
#
# def test_parquet_experiment():
#     df = pd.DataFrame(['a', 'b'])
#     print(df.head())
#
#     s = pd.Series(index=df.index)
#     s[0] = ','.join(['t1', 't2'])
#     s[1] = ','.join(['s1', 's2'])
#
#     df['ar'] = s
#
#     print(df.head())
#
#     pt = pa.Table.from_pandas(df)  # @UndefinedVariable
#     assert pt is not None
import pytest
from variants.parquet_io import family_variants_table,\
    save_family_variants_df_to_parquet, read_family_variants_df_from_parquet,\
    save_ped_df_to_parquet, read_ped_df_from_parquet
from variants.tests.common import assert_annotation_equals


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio",
])
def test_parquet_variants(variants_vcf, fixture_name, temp_filename):
    fvars = variants_vcf(fixture_name)
    table = family_variants_table(
        fvars.query_variants(
            inhteritance="not reference"
        ))
    assert table is not None

    df = table.to_pandas()
    print(df.head())

    save_family_variants_df_to_parquet(df, temp_filename)

    df1 = read_family_variants_df_from_parquet(temp_filename)
    assert df1 is not None
    print(df1.head())

    assert_annotation_equals(df, df1)


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio",
])
def test_parquet_pedigree(variants_vcf, fixture_name, temp_filename):
    fvars = variants_vcf(fixture_name)

    ped_df = fvars.ped_df
    print(ped_df.head())

    save_ped_df_to_parquet(ped_df, temp_filename)

    ped_df1 = read_ped_df_from_parquet(temp_filename)
    assert ped_df1 is not None
    print(ped_df1.head())

    assert_annotation_equals(ped_df, ped_df1)
