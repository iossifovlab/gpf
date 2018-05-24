'''
Created on Mar 23, 2018

@author: lubo
'''
from variants.variant import EffectGene, AlleleSummary
import pytest


def test_effect_gene_serialization():
    eg = EffectGene('a', 'b')

    assert str(eg) == 'a:b'


@pytest.mark.slow
def test_summary_variants_full(nvcf19f):
    for _index, row in nvcf19f.annot_df.iterrows():
        sv = AlleleSummary.from_dict(row)
        assert sv is not None
