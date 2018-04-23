'''
Created on Mar 8, 2018

@author: lubo
'''
from __future__ import print_function

from variants.vcf_utils import mat2str
import pytest


@pytest.mark.slow
def test_query_effect_types(nvcf19f):
    vs = nvcf19f.query_variants(
        inheritance='not reference',
        effect_types=['frame-shift', 'nonsense', 'splice-site', 'missense'])

    for v in vs:
        print(v, v.family_id, mat2str(v.best_st), v.falt_alleles, sep='\t')
        for aa in v.falt_alleles:
            print("\t:>", v.effects[aa].worst,
                  v.effects[aa].genes, v['all.nAltAlls'][aa],
                  v['all.altFreq'][aa], sep='\t')
