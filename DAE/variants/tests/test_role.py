'''
Created on Feb 13, 2018

@author: lubo
'''
from variants.roles import Role, RoleQuery
from variants.roles import RoleQuery as RQ


def test_role_all_simple():
    assert Role.all.value & Role.prb.value


def test_role_all():
    for role in Role:
        print(role.name)
        assert role.value & Role.all.value


def test_role_query():
    query = RQ.role(Role.prb).\
        or_(RQ.role(Role.sib)). \
        and_not_(RQ.role(Role.mom)).\
        and_not_(RQ.role(Role.dad))

    assert query.match([Role.prb])
    assert query.match([Role.sib])

    assert not query.match([Role.mom])
    assert not query.match([Role.dad])


def test_role_query_expression():

    query = RQ.role(Role.prb).\
        and_not_(RQ.role(Role.mom).
                 or_(RQ.role(Role.dad)))

    assert query.match([Role.prb])
    assert not query.match([Role.mom])
    assert not query.match([Role.dad])


def test_convert_from_name():
    role = Role.from_name("prb")
    assert role is not None
    assert isinstance(role, Role)

    assert role == Role.prb


def test_convert_from_bad_name():
    role = Role.from_name("ala_bala")
    assert role is not None
    assert isinstance(role, Role)

    assert role == Role.unknown


def test_role_query_from_list():
    rq = RoleQuery.any_([Role.prb, Role.sib])

    assert rq.match([Role.prb])
    assert rq.match([Role.sib])

    assert not rq.match([Role.dad])
