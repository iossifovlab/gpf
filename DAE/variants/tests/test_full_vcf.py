'''
Created on Mar 16, 2018

@author: lubo
'''
from __future__ import print_function
from variants.raw_vcf import RawFamilyVariants
from variants.vcf_utils import mat2str


def test_open_raw_vcf_with_region(vcf19_config, composite_annotator):
    region = "7:120008905-121036422"
    fvars = RawFamilyVariants(
        vcf19_config, region=region, annotator=composite_annotator)
    assert fvars is not None

    vs = fvars.query_variants(
        role='prb',
        effect_types=['frame-shift', 'nonsense', 'splice-site'])
    for c, v in enumerate(vs):
        print(c, v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene)
