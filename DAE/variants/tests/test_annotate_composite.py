'''
Created on Mar 7, 2018

@author: lubo
'''
from variants.raw_vcf import RawFamilyVariants
# from variants.loader import RawVariantsLoader
import pytest


@pytest.mark.slow
def test_annotate_on_load_vcf19(nvcf19_config, composite_annotator):
    annotator = composite_annotator

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
