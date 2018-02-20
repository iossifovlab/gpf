'''
Created on Feb 20, 2018

@author: lubo
'''
from pheno.common import Role
from variants.roles import RoleQuery


def test_query_by_filter(uagre):
    genes = ['KIAA1751']

    rq1 = RoleQuery(Role.dad)
    rq2 = RoleQuery(Role.mom)

    vs = uagre.query_variants(
        genes=genes,
        filter=lambda v: v.present_in_roles(rq1) and
        not v.present_in_roles(rq2)
    )
    vl = list(vs)
    assert len(vl) == 36
