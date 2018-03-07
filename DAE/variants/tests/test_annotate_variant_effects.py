'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

from variants.loader import RawVariantsLoader
from variants.tests.common import assert_annotation_equals


def test_annotate_variant_effects_ustudy(
        ustudy, temp_filename, effect_annotator):

    annotator = effect_annotator
    vars_df = annotator.annotate(ustudy.vars_df, ustudy.vcf_vars)

    stored_df = vars_df.copy()
    RawVariantsLoader.save_annotation_file(
        vars_df, temp_filename, storage='csv')
    assert_annotation_equals(vars_df, stored_df)

    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, storage='csv')
    assert_annotation_equals(vars_df, vars1_df)


@pytest.mark.skip
def test_annotate_variant_effects_nvcf(nvcf, effect_annotator):
    annotator = effect_annotator
    annotator.annotate(nvcf.vars_df, nvcf.vcf_vars)


@pytest.mark.skip
def test_annotate_variant_effects_uvcf(uvcf, effect_annotator):
    annotator = effect_annotator
    annotator.annotate(uvcf.vars_df, uvcf.vcf_vars)


@pytest.mark.skip
def test_annotate_variant_effects_fvcf(fvcf, effect_annotator):
    annotator = effect_annotator
    annotator.annotate(fvcf.vars_df, fvcf.vcf_vars)


def test_annotator_variants_effects_csv_experiment(
        nvcf19, temp_filename, effect_annotator):

    annotator = effect_annotator
    assert annotator is not None

    vars_df = annotator.annotate(nvcf19.vars_df, nvcf19.vcf_vars)
    assert vars_df is not None

    stored_df = vars_df.copy()
    RawVariantsLoader.save_annotation_file(
        vars_df, temp_filename, storage='csv')
    assert_annotation_equals(vars_df, stored_df)

    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, storage='csv')
    assert_annotation_equals(vars_df, vars1_df)
