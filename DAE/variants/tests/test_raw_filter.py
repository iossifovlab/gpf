'''
Created on Feb 20, 2018

@author: lubo
'''
from __future__ import print_function
from variants.attributes import Role
from variants.attributes_query import role_query
from variants.attributes_query_builder import any_node, token

# import pytest


# @pytest.mark.skip
def test_query_by_filter(ustudy_single):
    genes = ['NOC2L']

    rq1 = role_query.parse_and_transform("dad")
    rq2 = role_query.parse_and_transform("maternal_cousin")
    rq = "dad and not maternal_cousin"

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
        r1 = rq1.match(vals)
        r2 = rq2.match(vals)
        return r1 and (not r2)
    assert ffun(vals)

    vs = ustudy_single.query_variants(
        genes=genes,
        roles=rq
    )
    vl = list(vs)
    assert len(vl) == 13

    vs = ustudy_single.query_variants(
        genes=genes,
        filter=lambda v: ffun(v.variant_in_roles)
    )
    vl = list(vs)
    assert len(vl) == 13
