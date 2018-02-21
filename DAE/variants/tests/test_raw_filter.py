'''
Created on Feb 20, 2018

@author: lubo
'''
from pheno.common import Role
from variants.roles import RoleQuery


def test_query_by_filter(uagre):
    genes = ['NOC2L']

    rq1 = RoleQuery(Role.dad)
    rq2 = RoleQuery(Role.mom)

    vs = uagre.query_variants(
        genes=genes,
        filter=lambda v: rq1.match(
            RoleQuery.from_list(v.variant_in_roles)) and
        not rq2.match(RoleQuery.from_list(v.variant_in_roles))
    )
    vl = list(vs)
    assert len(vl) == 35
