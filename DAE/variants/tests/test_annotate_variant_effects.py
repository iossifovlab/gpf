'''
Created on Mar 6, 2018

@author: lubo
'''
from variants.annotate_variant_effects import VariantEffectsAnnotator
import pytest


def test_annotate_variant_effects_ustudy(ustudy):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(ustudy.vars_df, ustudy.vcf_vars)


@pytest.mark.slow
def test_annotate_variant_effects_nvcf(nvcf):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(nvcf.vars_df, nvcf.vcf_vars)


@pytest.mark.slow
def test_annotate_variant_effects_uvcf(uvcf):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(uvcf.vars_df, uvcf.vcf_vars)


@pytest.mark.veryslow
def test_annotate_variant_effects_fvcf(fvcf):
    annotator = VariantEffectsAnnotator()
    annotator.annotate(fvcf.vars_df, fvcf.vcf_vars)


def test_annotate_variant_effects_nvcf19(nvcf19):
    annotator = VariantEffectsAnnotator()
    vars_df = annotator.annotate(nvcf19.vars_df, nvcf19.vcf_vars)
    print(vars_df.head())
