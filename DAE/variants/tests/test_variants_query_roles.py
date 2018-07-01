'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function


def test_query_role_dad(variants_vcf):
    fvars = variants_vcf('fixtures/trios2_11541')
    vs = fvars.query_variants(roles='dad')
    vs = list(vs)
    print(vs)


def test_query_roles_dad(ustudy_vcf):
    genes = ['NOC2L']

    role_query = "dad"
    vs = ustudy_vcf.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 34


def test_query_roles_mom(ustudy_vcf):
    genes = ['NOC2L']

    role_query = "mom"
    vs = ustudy_vcf.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 36


def test_query_roles_prb(ustudy_vcf):
    genes = ['NOC2L']
    role_query = "prb"

    vs = ustudy_vcf.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 33


def test_query_roles_grandparents(ustudy_vcf):
    genes = ['NOC2L']

    role_query = "any(maternal_grandmother, maternal_grandfather)"
    vs = ustudy_vcf.query_variants(roles=role_query, genes=genes)
    vl = list(vs)

    assert len(vl) == 37


def test_query_roles_grandparents_string(ustudy_vcf):
    genes = ['NOC2L']

    vs = ustudy_vcf.query_variants(
        roles='any(maternal_grandmother, maternal_grandfather)',
        genes=genes)
    vl = list(vs)

    assert len(vl) == 37
