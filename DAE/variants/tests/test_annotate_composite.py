'''
Created on Mar 7, 2018

@author: lubo
'''
from variants.raw_vcf import RawFamilyVariants


def test_annotate_on_load_vcf19(ustudy_config, composite_annotator):
    annotator = composite_annotator

    fvariants = RawFamilyVariants(ustudy_config, annotator=annotator)
    assert fvariants is not None
