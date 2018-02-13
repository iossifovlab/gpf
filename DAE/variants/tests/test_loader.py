'''
Created on Feb 7, 2018

@author: lubo
'''
from variants.loader import VariantMatcher


def test_load_summary(uagre_loader):
    summary = uagre_loader.load_summary()
    assert summary is not None
    assert 'effectDetails' in summary.columns
    print(summary['effectDetails'].str.len().max())
    maxlen = summary[summary['effectDetails'].str.len() == 446]
    print(maxlen['effectDetails'])
    print(maxlen['effectGene'])

    print(summary.head())

# def test_load_pedigree(uagre_loader):
#     pedigree = uagre_loader.load_pedigree()
#     assert pedigree is not None
#
#
# def test_load_vcf(uagre_loader):
#     vs = uagre_loader.load_vcf()
#     assert vs is not None


def test_matcher(uagre_config):
    matcher = VariantMatcher(uagre_config)
    matcher.match()
    assert len(matcher.vars_df) == len(matcher.vcf_vars)
