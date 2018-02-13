'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from variants.roles import Role, RoleQuery


def test_query_roles_dad(uagre_study):
    genes = ['KIAA1751']
    df = uagre_study.query_genes(genes)

    role_query = RoleQuery(Role.dad)
    res_df, variants = uagre_study.query_roles([role_query], df)
    assert len(res_df) == 28
    assert len(variants) == 28


def test_query_roles_mom(uagre_study):
    genes = ['KIAA1751']
    df = uagre_study.query_genes(genes)

    role_query = RoleQuery(Role.mom)
    res_df, variants = uagre_study.query_roles([role_query], df)
    assert len(res_df) == 181
    assert len(variants) == 181


def test_query_roles_prb(uagre_study):
    genes = ['KIAA1751']
    df = uagre_study.query_genes(genes)

    role_query = RoleQuery(Role.prb)
    res_df, variants = uagre_study.query_roles([role_query], df)
    assert len(res_df) == 174
    assert len(variants) == 174


def test_query_roles_grandparents(uagre_study):
    genes = ['KIAA1751']
    df = uagre_study.query_genes(genes)

    role_query = RoleQuery(Role.maternal_grandmother). \
        or_(Role.maternal_grandfather)
    res_df, variants = uagre_study.query_roles([role_query], df)

    assert len(res_df) == 188
    assert len(variants) == 188
