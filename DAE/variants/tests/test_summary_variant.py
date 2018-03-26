'''
Created on Mar 23, 2018

@author: lubo
'''
from variants.summary_variant import EffectGene, SummaryVariantFull


def test_effect_gene_serialization():
    eg = EffectGene('a', 'b')

    assert str(eg) == 'a:b'


def test_summary_variants_full(nvcf19f):
    for index, row in nvcf19f.annot_df.iterrows():
        sv = SummaryVariantFull.from_annot_df(row)
        assert sv is not None
