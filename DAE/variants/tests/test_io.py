'''
Created on May 30, 2018

@author: lubo
'''
import pytest
from variants.loader import RawVariantsLoader
from variants.tests.common import assert_annotation_equals


@pytest.mark.parametrize("fixture_name,storage", [
    ("fixtures/effects_trio_multi", "csv"),
    ("fixtures/effects_trio", "csv")
])
def test_serialize_csv(fixture_name, full_vcf, storage, temp_filename):
    fvars = full_vcf(fixture_name)

    assert fvars.annot_df is not None

    outfile = temp_filename
    # outfile = "annot.tmp"

    RawVariantsLoader.save_annotation_file(
        fvars.annot_df, outfile, storage=storage)
    annot_df = RawVariantsLoader.load_annotation_file(
        outfile, storage=storage)
    assert annot_df is not None

    assert_annotation_equals(annot_df, fvars.annot_df)


@pytest.mark.slow
def test_serialize_csv_vcf19(nvcf19f, temp_filename):
    fvars = nvcf19f

    assert fvars.annot_df is not None

    outfile = temp_filename
    # outfile = "annot.tmp"

    RawVariantsLoader.save_annotation_file(
        fvars.annot_df, outfile, storage='csv')
    annot_df = RawVariantsLoader.load_annotation_file(
        outfile, storage='csv')
    assert annot_df is not None

    assert_annotation_equals(annot_df, fvars.annot_df)
