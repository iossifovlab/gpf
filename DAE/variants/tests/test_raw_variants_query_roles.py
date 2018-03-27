'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from variants.attributes import Role, RoleQuery


def test_query_roles_dad(ustudy_single):
    genes = ['NOC2L']

    role_query = RoleQuery.any_of(Role.dad)
    vs = ustudy_single.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 34


def test_query_roles_mom(ustudy_single):
    genes = ['NOC2L']

    role_query = RoleQuery.any_of(Role.mom)
    vs = ustudy_single.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 36


def test_query_roles_prb(ustudy_single):
    genes = ['NOC2L']
    role_query = RoleQuery.any_of(Role.prb)

    vs = ustudy_single.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 33


def test_query_roles_grandparents(ustudy_single):
    genes = ['NOC2L']

    role_query = RoleQuery.any_of(
        Role.maternal_grandmother, Role.maternal_grandfather)
    vs = ustudy_single.query_variants(roles=role_query, genes=genes)
    vl = list(vs)

    assert len(vl) == 37


def test_query_roles_grandparents_string(ustudy_single):
    genes = ['NOC2L']

    vs = ustudy_single.query_variants(
        roles='any(maternal_grandmother, maternal_grandfather)',
        genes=genes)
    vl = list(vs)

    assert len(vl) == 37
