'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from variants.roles import Role, RoleQuery


def test_query_roles_dad(uagre):
    genes = ['KIAA1751']
    df = uagre.query_genes(genes, uagre.vars_df)

    role_query = RoleQuery(Role.dad)
    variants = uagre.query_roles([role_query], df)
    assert len(list(variants)) == 28


def test_query_roles_mom(uagre):
    genes = ['KIAA1751']
    df = uagre.query_genes(genes, uagre.vars_df)

    role_query = RoleQuery(Role.mom)
    variants = uagre.query_roles([role_query], df)
    assert len(list(variants)) == 181


def test_query_roles_prb(uagre):
    genes = ['KIAA1751']
    df = uagre.query_genes(genes, uagre.vars_df)

    role_query = RoleQuery(Role.prb)
    variants = uagre.query_roles([role_query], df)
    assert len(list(variants)) == 174


def test_query_roles_grandparents(uagre):
    genes = ['KIAA1751']
    df = uagre.query_genes(genes, uagre.vars_df)

    role_query = RoleQuery(Role.maternal_grandmother). \
        or_(Role.maternal_grandfather)
    variants = uagre.query_roles([role_query], df)

    assert len(list(variants)) == 188
