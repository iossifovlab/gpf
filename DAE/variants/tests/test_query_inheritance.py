'''
Created on Feb 23, 2018

@author: lubo
'''
from variants.attributes import Inheritance


def test_query_inheritance(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='denovo or omission')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert set([Inheritance.denovo, Inheritance.omission]) & \
            v.inheritance_in_members

    assert len(vl) == 139


def test_query_inheritance_denovo(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='denovo')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert Inheritance.denovo in v.inheritance_in_members

    assert len(vl) == 95


def test_query_inheritance_omission(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='omission')
    assert vs is not None
    vl = list(vs)

    for v in vl:
        assert Inheritance.omission in v.inheritance_in_members

    assert len(vl) == 44


def test_query_inheritance_other(ustudy_vcf):
    vs = ustudy_vcf.query_variants(inheritance='other')
    assert vs is not None
    vl = list(vs)

    assert len(vl) == 0
