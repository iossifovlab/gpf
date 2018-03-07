'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

from variants.annotate_variant_effects import VariantEffectsAnnotator
from variants.loader import RawVariantsLoader
from variants.tests.common import assert_annotation_equals


def test_annotate_variant_effects_ustudy(ustudy, temp_filename):
    annotator = VariantEffectsAnnotator()
    vars_df = annotator.annotate(ustudy.vars_df, ustudy.vcf_vars)

    stored_df = vars_df.copy()
    RawVariantsLoader.save_annotation_file(
        vars_df, temp_filename, storage='csv')
    assert_annotation_equals(vars_df, stored_df)

    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, storage='csv')
    assert_annotation_equals(vars_df, vars1_df)


@pytest.mark.skip
def test_annotate_variant_effects_nvcf(nvcf):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(nvcf.vars_df, nvcf.vcf_vars)


@pytest.mark.skip
def test_annotate_variant_effects_uvcf(uvcf):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(uvcf.vars_df, uvcf.vcf_vars)


@pytest.mark.skip
def test_annotate_variant_effects_fvcf(fvcf):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(fvcf.vars_df, fvcf.vcf_vars)


def test_annotate_variant_effects_nvcf19(nvcf19):
    annotator = VariantEffectsAnnotator()
    vars_df = annotator.annotate(nvcf19.vars_df, nvcf19.vcf_vars)
    print(vars_df.head())


def test_annotator_variants_effects_csv_experiment(nvcf19, temp_filename):

    annotator = VariantEffectsAnnotator()
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
