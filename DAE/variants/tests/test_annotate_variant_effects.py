'''
Created on Mar 6, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

from variants.loader import RawVariantsLoader
from variants.tests.common import assert_annotation_equals


@pytest.mark.slow
def test_annotate_variant_effects_ustudy(
        ustudy, temp_filename, effect_annotator):

    annotator = effect_annotator
    vars_df = annotator.annotate(ustudy.annot_df, ustudy.vcf_vars)

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
    annotator.annotate(nvcf.annot_df, nvcf.vcf_vars)


@pytest.mark.skip
def test_annotate_variant_effects_uvcf(uvcf, effect_annotator):
    annotator = effect_annotator
    annotator.annotate(uvcf.annot_df, uvcf.vcf_vars)


@pytest.mark.skip
def test_annotate_variant_effects_fvcf(fvcf, effect_annotator):
    annotator = effect_annotator
    annotator.annotate(fvcf.annot_df, fvcf.vcf_vars)


@pytest.mark.slow
def test_annotator_variants_effects_csv_experiment(
        nvcf19, temp_filename, effect_annotator):

    annotator = effect_annotator
    assert annotator is not None

    annot_df = annotator.annotate(nvcf19.annot_df, nvcf19.vcf_vars)
    assert annot_df is not None

    stored_df = annot_df.copy()
    RawVariantsLoader.save_annotation_file(
        annot_df, temp_filename, storage='csv')
    assert_annotation_equals(annot_df, stored_df)

    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, storage='csv')
    assert_annotation_equals(annot_df, vars1_df)


def test_effects_annotation(effect_annotator):
    chrom, pos, ref, alts = (
        "1",
        874816,
        'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT',
        [
            'C',
            'CTCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT',
            'CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
            'CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT'
        ]
    )

    for alt in alts:
        effects = effect_annotator.do_annotate_variant(chrom, pos, ref, alt)
        print(effects)
