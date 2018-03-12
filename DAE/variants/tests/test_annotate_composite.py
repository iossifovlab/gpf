'''
Created on Mar 7, 2018

@author: lubo
'''
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.raw_vcf import RawFamilyVariants


def test_annotate_composite_simple(ustudy, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    annotator.setup(ustudy)
    annot_df = annotator.annotate(ustudy.annot_df, ustudy.vcf_vars)
    assert annot_df is not None
    print(annot_df.head())


def test_annotate_composite_simple_vcf19(nvcf19, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    annotator.setup(nvcf19)
    vars_df = annotator.annotate(nvcf19.annot_df, nvcf19.vcf_vars)
    assert vars_df is not None
    print(vars_df.head())


def test_annotate_on_load(ustudy_config, ustudy, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    annotator.setup(ustudy)

    fvariants = RawFamilyVariants(ustudy_config, annotator=annotator)
    assert fvariants is not None


def test_annotate_on_load_vcf19(nvcf19_config, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    fvariants = RawFamilyVariants(nvcf19_config, annotator=annotator)
    assert fvariants is not None
