'''
Created on Mar 8, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

from variants.vcf_utils import mat2str


pytestmark = pytest.mark.xfail()


def test_query_effect_types(ustudy_vcf):
    vs = ustudy_vcf.query_variants(
        inheritance='not reference',
        effect_types=['frame-shift', 'nonsense', 'splice-site', 'missense'])

    for v in vs:
        print(v, v.family_id, mat2str(v.best_st), sep='\t')
        for sa in v.alt_alleles:
            print("\t:>", sa.effect.worst,
                  sa.effect.genes,
                  sa['af_alternative_alleles_count'],
                  sa['af_alternative_alleles_freq'], sep='\t')
