'''
Created on Mar 7, 2018

@author: lubo
'''
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VariantEffectsAnnotator
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator


def test_annotate_composite_simple(ustudy):
    annotator = AnnotatorComposite(annotators=[
        VariantEffectsAnnotator(),
        VcfAlleleFrequencyAnnotator(ustudy),
    ])

    vars_df = annotator.annotate(ustudy.vars_df, ustudy.vcf_vars)
    assert vars_df is not None
    print(vars_df.head())


def test_annotate_composite_simple_vcf19(nvcf19):
    annotator = AnnotatorComposite(annotators=[
        VariantEffectsAnnotator(),
        VcfAlleleFrequencyAnnotator(nvcf19),
    ])

    vars_df = annotator.annotate(nvcf19.vars_df, nvcf19.vcf_vars)
    assert vars_df is not None
    print(vars_df.head())
