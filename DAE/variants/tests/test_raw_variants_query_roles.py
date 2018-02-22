'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from variants.roles import Role, RoleQuery


def test_query_roles_dad(uagre):
    genes = ['NOC2L']

    role_query = RoleQuery.any_of(Role.dad)
    vs = uagre.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 34


def test_query_roles_mom(uagre):
    genes = ['NOC2L']

    role_query = RoleQuery.any_of(Role.mom)
    vs = uagre.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 36


def test_query_roles_prb(uagre):
    genes = ['NOC2L']
    role_query = RoleQuery.any_of(Role.prb)

    vs = uagre.query_variants(roles=role_query, genes=genes)
    vl = list(vs)
    assert len(vl) == 33


def test_query_roles_grandparents(uagre):
    genes = ['NOC2L']

    role_query = RoleQuery.any_of(
        Role.maternal_grandmother, Role.maternal_grandfather)
    vs = uagre.query_variants(roles=role_query, genes=genes)
    vl = list(vs)

    assert len(vl) == 37
