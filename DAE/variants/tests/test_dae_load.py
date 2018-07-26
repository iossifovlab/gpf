'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function

import os

import engarde.checks as ec
import numpy as np
import pyarrow.parquet as pq
from variants.raw_dae import RawDAE
from variants.vcf_utils import str2mat, best2gt
from variants.parquet_io import save_family_variants_to_parquet
import pytest


# def test_load_dae_summary_file():
#     filename = "/home/lubo/Work/seq-pipeline/data-hg19/cccc/w1202s766e611/transmissionIndex-HW-DNRM.txt.bgz"
#     region = Region("1", 1, 802298)
#
#     df = RawDAE.load_region(filename, region)
#     print("---------------------------------")
#     print("---------------------------------")
#     print(df.head())
#     print("---------------------------------")
def test_load_dae_summary(raw_dae, temp_filename):
    dae = raw_dae("fixtures/transmission")
    dae.load_families()

    assert dae is not None

    df = dae.load_summary_variants()
    assert df is not None
#     print(df.dtypes)

    ec.has_dtypes(
        df,
        {
            'chrom': object,
            'position': int,
            'reference': object,
            'alternative': object,
        })

    df = dae.load_summary_variants()
    print(df.head())
    print(df.dtypes)
    print(df.columns)

    for v in dae.wrap_summary_variants(df):
        print(v)

    table = dae.summary_table(df)
    pq.write_table(table, temp_filename)


@pytest.mark.skip
def test_load_dae_family(raw_dae, temp_dirname):
    dae = raw_dae("fixtures/transmission", "1")
    dae.load_families()

    f2 = dae.families['f2']
    assert len(f2) == 4

    assert dae is not None

    df = dae.load_family_variants()
    assert df is not None

    fname = os.path.join(temp_dirname, "f.parquet")
    aname = os.path.join(temp_dirname, "a.parquet")

    save_family_variants_to_parquet(
        dae.wrap_family_variants(df, return_reference=True),
        fname, aname, batch_size=1000)


def test_explode_family_genotype():
    fgt = RawDAE.explode_family_genotypes(
        'f3:2121/0101:11 27 34 13/0 26 0 15/0 0 0 0')
    print(fgt)


def test_str2mat():
    res = str2mat("2121/0101")
    assert res.dtype == np.int8
    assert np.all(res == np.array([[2, 1, 2, 1], [0, 1, 0, 1]], dtype=np.int8))


def test_best2gt():
    best = np.array([[2, 1, 2, 1], [0, 1, 0, 1]], dtype=np.int8)
    res = best2gt(best)
    assert np.all(res == np.array([[0, 1, 0, 1], [0, 0, 0, 0]], dtype=np.int8))

    best = np.array([[0, 1, 0, 1], [2, 1, 2, 1]], dtype=np.int8)
    res = best2gt(best)
    assert np.all(res == np.array([[1, 1, 1, 1], [1, 0, 1, 0]], dtype=np.int8))
