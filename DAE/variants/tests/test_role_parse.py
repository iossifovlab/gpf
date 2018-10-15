'''
Created on Feb 21, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
from variants.attributes import RoleQuery, Role


def test_role_query_parse_eq_simple():
    rq = RoleQuery.parse("eq(prb,sib)")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert not rq.match([Role.prb])
    assert not rq.match([Role.prb, Role.sib, Role.dad])


def test_role_query_parse_all_simple():
    rq = RoleQuery.parse("all(prb,sib)")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert not rq.match([Role.prb])


def test_role_query_parse_any_simple():
    rq = RoleQuery.parse("any(prb,sib)")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert rq.match([Role.prb])

    assert not rq.match([Role.dad])


def test_role_query_parse_and_simple():
    rq = RoleQuery.parse("prb and sib")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert not rq.match([Role.prb])


def test_role_query_parse_or_simple():
    rq = RoleQuery.parse("prb or sib")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert rq.match([Role.prb])

    assert not rq.match([Role.dad])


def test_role_query_parse_not_simple():
    rq = RoleQuery.parse("not prb")
    assert rq is not None

    assert rq.match([Role.sib])
    assert not rq.match([Role.prb])
    assert not rq.match([Role.sib, Role.prb])


def test_role_query_mixed_1():
    rq = RoleQuery.parse("mom and not (prb and sib)")
    assert rq is not None

    assert rq.match([Role.mom])
    assert rq.match([Role.mom, Role.dad])
    assert rq.match([Role.mom, Role.prb])
    assert rq.match([Role.mom, Role.sib])
    assert not rq.match([Role.mom, Role.prb, Role.sib])


def test_role_query_mixed_2():
    rq = RoleQuery.parse("mom and not (prb or sib)")
    assert rq is not None

    assert rq.match([Role.mom])
    assert rq.match([Role.mom, Role.dad])
    assert not rq.match([Role.mom, Role.prb])
    assert not rq.match([Role.mom, Role.sib])
    assert not rq.match([Role.mom, Role.prb, Role.sib])


def test_role_query_parse_bit_and_simple():
    rq = RoleQuery.parse("prb & sib")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert not rq.match([Role.prb])


def test_role_query_parse_bit_or_simple():
    rq = RoleQuery.parse("prb | sib")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert rq.match([Role.prb])

    assert not rq.match([Role.dad])


def test_role_query_parse_bit_multiple_or_simple():
    rq = RoleQuery.parse("prb | sib | mom | dad")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert rq.match([Role.dad, Role.mom])

    assert not rq.match([Role.maternal_grandfather])


def test_role_query_parse_multiple_or_simple():
    rq = RoleQuery.parse("prb or sib or mom or dad")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib])
    assert rq.match([Role.prb, Role.sib, Role.dad])
    assert rq.match([Role.dad, Role.mom])

    assert not rq.match([Role.maternal_grandfather])


def test_role_query_parse_multiple_and_simple():
    rq = RoleQuery.parse("prb and sib and mom and dad")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib, Role.mom, Role.dad])

    assert not rq.match([Role.dad, Role.mom])
    assert not rq.match([Role.prb, Role.sib])
    assert not rq.match([Role.maternal_grandfather])


def test_role_query_parse_multiple_bit_and_simple():
    rq = RoleQuery.parse("prb & sib & mom & dad")
    assert rq is not None

    assert rq.match([Role.prb, Role.sib, Role.mom, Role.dad])

    assert not rq.match([Role.dad, Role.mom])
    assert not rq.match([Role.prb, Role.sib])
    assert not rq.match([Role.maternal_grandfather])
