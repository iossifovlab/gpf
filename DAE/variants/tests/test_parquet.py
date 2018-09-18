'''
Created on Mar 7, 2018

@author: lubo
'''
from __future__ import print_function
import pytest
from variants.parquet_io import family_variants_table,\
    save_ped_df_to_parquet, read_ped_df_from_parquet, \
    save_family_allele_df_to_parquet,\
    read_family_allele_df_from_parquet, summary_table
from variants.tests.common_tests_helpers import assert_annotation_equals
import os
import pyarrow.parquet as pq
import pandas as pd


@pytest.mark.parametrize("fixture_name", [
    "fixtures/effects_trio_multi",
    "fixtures/effects_trio",
])
def test_parquet_variants(variants_vcf, fixture_name, temp_filename):
    fvars = variants_vcf(fixture_name)
    variants = fvars.query_variants(
        return_reference=True,
        return_unknown=True
    )
    for allele_table in family_variants_table(variants):
        df = allele_table.to_pandas()
        save_family_allele_df_to_parquet(df, temp_filename)

        df1 = read_family_allele_df_from_parquet(temp_filename)
        assert df1 is not None
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


@pytest.mark.skip
@pytest.mark.parametrize("fixture_name", [
    "fixtures/parquet_trios",
    # "fixtures/effects_trio",
])
def test_experiment_with_parquet_partitioned_datasets(
        variants_vcf, fixture_name, temp_dirname):

    fvars = variants_vcf(fixture_name)
    summary_variants_table = summary_table(fvars.annot_df)
    # ped_df = fvars.ped_df

    variants = fvars.query_variants(
        return_reference=True,
        return_unknown=True)

    summary_dataset_filename = os.path.join(
        temp_dirname, "summary.dataset")
    print(("summary:>>", summary_dataset_filename))
    pq.write_to_dataset(
        summary_variants_table,
        root_path=summary_dataset_filename,
        partition_cols=["chrom"])

    family_dataset_filename = os.path.join(temp_dirname, "family.dataset")
    allele_dataset_filename = os.path.join(temp_dirname, "allele.dataset")

    for family_table, allele_table in family_variants_table(variants):

        print(("family:>>", family_dataset_filename))
        pq.write_to_dataset(
            family_table,
            root_path=family_dataset_filename,
            partition_cols=["chrom", "family_index"],
            preserve_index=False)

        print(("allele:>>", allele_dataset_filename))
        pq.write_to_dataset(
            allele_table,
            root_path=allele_dataset_filename,
            partition_cols=["chrom", "family_index"],
            preserve_index=False)

    allele_table2 = pq.read_table(allele_dataset_filename)
    assert allele_table2 is not None
    print(allele_table2)
    allele_df2 = allele_table2.to_pandas()
    allele_df2 = allele_df2.sort_values(
        by=["family_variant_index", "summary_variant_index",
            "allele_index", "family_index"])
    print(allele_df2)

    allele_df = allele_table.to_pandas()
    print(allele_df)

    allele_df2.chrom = pd.Series(allele_df2.chrom.astype(str))
    print(allele_df2.chrom)
    print(allele_df.chrom)

    assert_annotation_equals(allele_df, allele_df2)
