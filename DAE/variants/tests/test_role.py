'''
Created on Feb 13, 2018

@author: lubo
'''
from variants.roles import Role
from variants.roles import RoleQuery as rq


def test_role_all_simple():
    assert Role.all.value & Role.prb.value


def test_role_all():
    for role in Role:
        print(role.name)
        assert role.value & Role.all.value


def test_role_query():
    query = rq(Role.prb).or_(Role.sib). \
        and_not_(Role.mom).and_not_(Role.dad)

    assert query.value & Role.prb.value
    assert query.value & Role.sib.value

    assert not (query.value & Role.mom.value)
    assert not (query.value & Role.dad.value)


def test_role_query_expression():

    query = rq(Role.prb).and_not_(rq(Role.mom).or_(Role.dad))

    assert query.value & Role.prb.value
    assert not (query.value & Role.mom.value)
    assert not (query.value & Role.dad.value)


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
