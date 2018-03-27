'''
Created on Feb 23, 2018

@author: lubo
'''


def test_query_inheritance(ustudy_single):
    vs = ustudy_single.query_variants(inheritance='denovo or omission')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert v.is_denovo() or v.is_omission()

    assert len(vl) == 137


def test_query_inheritance_denovo(ustudy_single):
    vs = ustudy_single.query_variants(inheritance='denovo')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert v.is_denovo()

    assert len(vl) == 94


def test_query_inheritance_omission(ustudy_single):
    vs = ustudy_single.query_variants(inheritance='omission')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert v.is_omission()

    assert len(vl) == 43


def test_query_inheritance_other(ustudy_single):
    vs = ustudy_single.query_variants(inheritance='other')
    assert vs is not None
    vl = list(vs)

    assert len(vl) == 0
