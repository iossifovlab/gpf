'''
Created on Feb 23, 2018

@author: lubo
'''


def test_query_inheritance(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='denovo or omission')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert v.is_denovo() or v.is_omission()

    assert len(vl) == 139


def test_query_inheritance_denovo(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='denovo')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert v.is_denovo()

    assert len(vl) == 95


def test_query_inheritance_omission(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='omission')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert v.is_omission()

    assert len(vl) == 44


def test_query_inheritance_other(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='other')
    assert vs is not None
    vl = list(vs)

    assert len(vl) == 0


def test_query_inheritance_reference(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='reference')
    assert vs is not None
    vl = list(vs)

    assert len(vl) == 0


def test_query_inheritance_not_reference(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='not reference')
    assert vs is not None
    vl = list(vs)

    assert len(vl) == 511
