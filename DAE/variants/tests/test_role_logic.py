'''
Created on Feb 21, 2018

@author: lubo
'''
from variants.attributes import Role
from variants.attributes import RoleQuery as RQ


def test_role_any():
    rq = RQ.any_of(Role.mom, Role.dad)
    assert not rq.match([Role.prb])
    assert rq.match([Role.prb, Role.mom])
    assert rq.match([Role.prb, Role.dad])
    assert rq.match([Role.prb, Role.mom, Role.dad])


def test_role_all():
    rq = RQ.all_of(Role.prb, Role.sib)
    assert rq.match([Role.prb, Role.sib])

    assert not rq.match([Role.prb])
    assert not rq.match([Role.prb, Role.mom])
    assert not rq.match([Role.prb, Role.dad])
    assert rq.match([Role.prb, Role.sib, Role.dad])


def test_role_eq():
    rq = RQ.eq_of(Role.prb, Role.sib)
    assert rq.match([Role.prb, Role.sib])

    assert not rq.match([Role.prb])
    assert not rq.match([Role.sib])
    assert not rq.match([Role.prb, Role.mom])
    assert not rq.match([Role.prb, Role.dad])
    assert not rq.match([Role.prb, Role.sib, Role.dad])


def test_and_simple():
    rq = RQ.any_of(Role.prb).and_(RQ.any_of(Role.mom))
    assert rq.match([Role.prb, Role.mom])
    assert not rq.match([Role.prb])
    assert not rq.match([Role.mom])


def test_and_any_simple():
    rq = RQ.any_of(Role.prb).and_(RQ.any_of(Role.mom, Role.dad))
    assert rq.match([Role.prb, Role.mom])
    assert rq.match([Role.prb, Role.dad])
    assert not rq.match([Role.prb])
    assert not rq.match([Role.mom])
    assert not rq.match([Role.dad])


def test_and_all_simple():
    rq = RQ.any_of(Role.prb).and_(RQ.all_of(Role.mom, Role.dad))
    assert rq.match([Role.prb, Role.mom, Role.dad])
    assert not rq.match([Role.prb, Role.mom])
    assert not rq.match([Role.prb, Role.dad])
    assert not rq.match([Role.prb])
    assert not rq.match([Role.mom])
    assert not rq.match([Role.dad])


def test_and_not_all_simple():
    rq = RQ.any_of(Role.prb).and_not_(RQ.all_of(Role.mom, Role.dad))
    assert rq.match([Role.prb, Role.mom])
    assert rq.match([Role.prb, Role.dad])
    assert rq.match([Role.prb])

    assert not rq.match([Role.prb, Role.mom, Role.dad])

    assert not rq.match([Role.mom, Role.dad])
    assert not rq.match([Role.sib])


def test_and_not_any_simple():
    rq = RQ.any_of(Role.prb).and_not_(RQ.any_of(Role.mom, Role.dad))
    assert rq.match([Role.prb])

    assert not rq.match([Role.prb, Role.mom])
    assert not rq.match([Role.prb, Role.dad])
    assert not rq.match([Role.prb, Role.mom, Role.dad])

    assert not rq.match([Role.mom, Role.dad])
    assert not rq.match([Role.sib])
