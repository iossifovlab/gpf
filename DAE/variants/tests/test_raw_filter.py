'''
Created on Feb 20, 2018

@author: lubo
'''
from __future__ import print_function
from pheno.common import Role
from variants.roles import RoleQuery
import pytest


@pytest.mark.skip
def test_query_by_filter(uagre):
    genes = ['NOC2L']

    rq1 = RoleQuery.role(Role.dad)
    rq2 = RoleQuery.role(Role.maternal_cousin)

    vals = [
        Role.maternal_aunt,
        Role.maternal_grandfather,
        Role.maternal_grandmother,
        Role.mom,
        Role.dad,
        Role.sib,
        Role.prb
    ]

    assert rq1.match(vals)
    assert not rq2.match(vals)

    def ffun(vals):
        print("FFUN:", vals)
        return (rq1.match(vals)
                and (not rq2.match(vals)))
    print(ffun(vals))
    assert ffun(vals)

    vs = uagre.query_variants(
        genes=genes,
        filter=lambda v: ffun(v.variant_in_roles)
    )
    vl = list(vs)
    assert len(vl) == 35
