'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function

from variants.raw_dae import RawDAE
from RegionOperations import Region
from variants.tests.common_tests_helpers import relative_to_this_test_folder
import os
import engarde.checks as ec


# def test_load_dae_summary_file():
#     filename = "/home/lubo/Work/seq-pipeline/data-hg19/cccc/w1202s766e611/transmissionIndex-HW-DNRM.txt.bgz"
#     region = Region("1", 1, 802298)
#
#     df = RawDAE.load_region(filename, region)
#     print("---------------------------------")
#     print("---------------------------------")
#     print(df.head())
#     print("---------------------------------")


def test_load_dae_summary(default_genome):
    summary_filename = relative_to_this_test_folder(
        "fixtures/transmission.txt.gz")
    assert os.path.exists(summary_filename)
    toomany_filename = relative_to_this_test_folder(
        "fixtures/transmission-TOOMANY.txt.gz")
    assert os.path.exists(toomany_filename)

    family_filename = relative_to_this_test_folder(
        "fixtures/family_simple.txt")

    dae = RawDAE(summary_filename, toomany_filename, family_filename,
                 region=None,
                 genome=default_genome,
                 annotator=None)

    assert dae is not None

    df = dae.load_summary_variants()
    assert df is not None
    print(df.dtypes)

    ec.has_dtypes(
        df,
        {
            'chrom': object,
            'position': int,
            'reference': object,
            'alternative': object,
        })
