'''
Created on Apr 24, 2017

@author: lubo
'''
from enrichment_tool.genotype_helper import GenotypeHelper as GH


def test_studies_variants_unaffected_with_effect_type_lgd(unaffected_studies):
    variants = GH. \
        from_studies(unaffected_studies, 'sib'). \
        get_variants('LGDs')
    variants = list(variants)

    seen = set()
    for v in variants:
        assert 'sib' in v.inChS
        v_key = v.familyId + v.location + v.variant
        assert v_key not in seen
        seen.add(v_key)

    assert 232 == len(variants)


def test_variants_unaffected_with_effect_type_lgd(sd, unaffected_studies):
    gh = GH.from_dataset(sd, 'phenotype', 'unaffected')

    variants = gh.get_variants('LGDs')
    assert variants is not None
    variants = list(variants)

    other_variants = GH. \
        from_studies(unaffected_studies, 'sib'). \
        get_variants('LGDs')
    other_variants = list(other_variants)

    seen = set()
    for v in variants:
        assert 'sib' in v.inChS
        v_key = v.familyId + v.location + v.variant
        assert v_key not in seen
        seen.add(v_key)

    for ov in other_variants:
        found = False
        for v in variants:
            if v.familyId == ov.familyId and \
                    v.location == ov.location and \
                    v.variant == ov.variant:
                found = True
                break
        if not found:
            print(
                "Not Found:",
                ov.familyId, ov.location, ov.study.name,
                ov.inChS, ov.variant, ov.geneEffect)

    for ov in variants:
        found = False
        for v in other_variants:
            if v.familyId == ov.familyId and \
                    v.location == ov.location and \
                    v.variant == ov.variant:
                found = True
                break
        if not found:
            print(
                "Not Found:",
                ov.familyId, ov.location, ov.study.name,
                ov.inChS, ov.variant, ov.geneEffect)

    assert 232 == len(other_variants)
    assert len(other_variants) == len(variants)


def test_variants_autism_with_effect_type_lgd(sd):
    # gh = GH.from_studies(autism_studies, 'prb')
    gh = GH.from_dataset(sd, 'phenotype', 'autism')

    variants = gh.get_variants('LGDs')
    assert variants is not None

    count = 0
    for v in variants:
        assert 'prb' in v.inChS
        count += 1
    print(count)
    assert 607 == count
