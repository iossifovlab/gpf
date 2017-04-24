'''
Created on Apr 24, 2017

@author: lubo
'''
from enrichment_tool.genotype_helper import GenotypeHelper as GH


def test_variants_unaffected_with_effect_type_lgd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'unaffected')

    variants = gh.get_variants('LGDs')
    assert variants is not None

    count = 0
    for v in variants:
        assert 'sib' in v.inChS
        count += 1
    print(count)
    assert 243 == count
