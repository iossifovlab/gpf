'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from variants.roles import Role, RoleQuery


def test_query_roles_dad(uagre):
    genes = ['KIAA1751']

    role_query = RoleQuery(Role.dad)
    vs = uagre.query_variants(roles=[role_query], genes=genes)
    vl = list(vs)
    assert len(vl) == 36


def test_query_roles_mom(uagre):
    genes = ['KIAA1751']

    role_query = RoleQuery(Role.mom)
    vs = uagre.query_variants(roles=[role_query], genes=genes)
    vl = list(vs)
    assert len(vl) == 200


def test_query_roles_prb(uagre):
    genes = ['KIAA1751']
    role_query = RoleQuery(Role.prb)

    vs = uagre.query_variants(roles=[role_query], genes=genes)
    vl = list(vs)
    assert len(vl) == 193


def test_query_roles_grandparents(uagre):
    genes = ['KIAA1751']

    role_query = RoleQuery(Role.maternal_grandmother). \
        or_(Role.maternal_grandfather)
    vs = uagre.query_variants(roles=[role_query], genes=genes)
    vl = list(vs)

    assert len(vl) == 195
