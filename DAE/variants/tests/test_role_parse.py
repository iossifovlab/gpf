'''
Created on Feb 21, 2018

@author: lubo
'''
from __future__ import print_function
import ast
from variants.roles import RoleQuery, Role


def test_simple():
    tree = ast.parse("print('hello')")
    print(tree)

    tree = ast.parse("eq(prb,sib)")
    print(ast.dump(tree))

    tree = ast.parse("eq(prb,sib)", mode='eval')
    print(ast.dump(tree))

    tree = ast.parse("mom and any(prb,sib)", mode='eval')
    print(ast.dump(tree))

    tree = ast.parse("mom and not any(prb,sib)", mode='eval')
    print(ast.dump(tree))

    tree = ast.parse("mom and not (prb and sib)", mode='eval')
    print(ast.dump(tree))


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
