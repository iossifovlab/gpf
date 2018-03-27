'''
Created on Mar 7, 2018

@author: lubo
'''
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.raw_vcf import RawFamilyVariants
# from variants.loader import RawVariantsLoader
import pytest


@pytest.mark.skip
def test_annotate_composite_simple(ustudy_single, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    annotator.setup(ustudy_single)
    annot_df = annotator.annotate(
        ustudy_single.annot_df, ustudy_single.vcf_vars)
    assert annot_df is not None
    print(annot_df.head())


@pytest.mark.skip
def test_annotate_composite_simple_vcf19(nvcf19s, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    annotator.setup(nvcf19s)
    vars_df = annotator.annotate(nvcf19s.annot_df, nvcf19s.vcf_vars)
    assert vars_df is not None
    print(vars_df.head())


@pytest.mark.skip
def test_annotate_on_load(ustudy_config, ustudy_single, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    annotator.setup(ustudy_single)

    fvariants = RawFamilyVariants(ustudy_config, annotator=annotator)
    assert fvariants is not None


@pytest.mark.slow
def test_annotate_on_load_vcf19(nvcf19_config, effect_annotator):
    annotator = AnnotatorComposite(annotators=[
        effect_annotator,
        VcfAlleleFrequencyAnnotator(),
    ])

    fvariants = RawFamilyVariants(nvcf19_config, annotator=annotator)
    assert fvariants is not None


# def test_do_annotate_test_nvcf19_files(nvcf19, composite_annotator):
#     RawVariantsLoader.save_annotation_file(
#         nvcf19.annot_df, "nvcf19-eff.tmp", storage='csv')
#
#
# def test_do_annotate_test_ustudy_files(ustudy_single, composite_annotator):
#     RawVariantsLoader.save_annotation_file(
#         ustudy_single.annot_df, "ustudy_single-eff.tmp", storage='csv')
