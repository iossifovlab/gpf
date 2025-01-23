# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.query_variants.attributes_query import (
    OrNode,
    inheritance_query,
    role_query,
)
from dae.query_variants.sql.schema2.sql_query_builder import SqlQueryBuilder
from dae.variants.attributes import Inheritance, Role
from studies.query_transformer import QueryTransformer


@pytest.mark.parametrize(
    "present_in_child,present_in_parent,inheritance,roles,accepted",
    [
        (
            {"proband only"},
            {"neither"},
            [Inheritance.denovo], [Role.prb], True),
        (
            {"proband only"},
            {"neither"},
            [Inheritance.denovo], [Role.sib], False),
        (
            {"proband only"},
            {"neither"},
            [Inheritance.mendelian], [Role.prb], False),
        (
            {"proband only", "sibling only"},
            {"neither"},
            [Inheritance.denovo], [Role.prb], True),
        (
            {"proband only", "sibling only"},
            {"neither"},
            [Inheritance.denovo], [Role.sib], True),
        (
            {"proband only", "sibling only"},
            {"neither"},
            [Inheritance.denovo], [Role.prb, Role.sib], False),
        (
            {"proband only", "sibling only", "proband and sibling"},
            {"neither"},
            [Inheritance.denovo], [Role.prb, Role.sib], True),
        (
            {"proband only"},
            {"mother only"},
            [Inheritance.mendelian], [Role.prb, Role.mom], True),
        (
            {"proband only"},
            {"mother only"},
            [Inheritance.denovo, Inheritance.mendelian],
            [Role.prb, Role.mom], True),
        (
            {"neither"},
            {"mother only"},
            [Inheritance.missing],
            [Role.mom], True),
        (
            {"proband only", "proband and sibling", "neither"},
            {"mother only", "neither"},
            [Inheritance.denovo, Inheritance.mendelian, Inheritance.missing],
            [Role.prb, Role.sib, Role.mom], True),
        (
            {"proband and sibling"},
            {"neither"},
            [Inheritance.denovo],
            [Role.prb, Role.sib], True),
    ],
)
def test_transform_present_in_child_and_present_in_parent(
    present_in_child: set[str],
    present_in_parent: set[str],
    inheritance: list[Inheritance],
    roles: list[Role],
    accepted: bool,  # noqa: FBT001
) -> None:

    roles_q = QueryTransformer._transform_present_in_child_and_parent_roles(
        present_in_child, present_in_parent)
    assert roles_q is not None
    roles_m = role_query.transform_tree_to_matcher(
        role_query.transform_query_string_to_tree(roles_q))

    inheritance_q = QueryTransformer\
        ._transform_present_in_child_and_parent_inheritance(
            present_in_child, present_in_parent)

    assert inheritance_q is not None

    inheritance_m = inheritance_query.transform_tree_to_matcher(
        inheritance_query.transform_query_string_to_tree(inheritance_q))

    roles_matched = roles_m.match(roles)
    inheritance_matched = inheritance_m.match(inheritance)

    assert (roles_m.match(roles) and inheritance_m.match(inheritance)) == \
        accepted, (roles_matched, inheritance_matched)


def test_attributes_query_roles() -> None:
    roles_q = "sib and not prb"
    roles_m = role_query.transform_tree_to_matcher(
        OrNode([role_query.transform_query_string_to_tree(roles_q)]))

    result = roles_m.match([Role.prb])
    assert not result


@pytest.mark.parametrize(
    "present_in_child,present_in_parent,accepted,rejected,expected_query", [
        ({"proband and sibling"},
         {"neither"},
         [Role.prb.value | Role.sib.value],
         [Role.prb.value, Role.sib.value,
          Role.prb.value | Role.sib.value | Role.mom.value],
         "(prb and sib) and (not mom and not dad)"),
        ({"neither"},
         {"neither"},
         [Role.unknown.value, Role.maternal_aunt.value],
         [Role.prb.value, Role.sib.value,
          Role.prb.value | Role.sib.value | Role.mom.value],
         "(not prb and not sib) and (not mom and not dad)"),
        ({"proband only", "sibling only", "proband and sibling"},
         {"father only"},
         [Role.prb.value | Role.dad.value],
         [Role.prb.value, Role.sib.value,
          Role.prb.value | Role.sib.value | Role.mom.value],
         "(( prb and not sib ) or ( sib and not prb ) or ( prb and sib )) "
         "and (dad and not mom)"),
    ])
def test_transform_present_in_child_and_present_in_parent_roles(
    present_in_child: set[str],
    present_in_parent: set[str],
    accepted: list[int],
    rejected: list[int],
    expected_query: str,
) -> None:
    roles_query = QueryTransformer._transform_present_in_child_and_parent_roles(
        present_in_child, present_in_parent)
    assert roles_query is not None
    assert roles_query == expected_query
    for value in accepted:
        assert SqlQueryBuilder.check_roles_query_value(roles_query, value)
    for value in rejected:
        assert not SqlQueryBuilder.check_roles_query_value(roles_query, value)


@pytest.mark.parametrize(
    "present_in_child,present_in_parent,accepted,rejected,expected_query", [
        ({"proband and sibling"},
         {"neither"},
         [Inheritance.denovo.value],
         [Inheritance.mendelian.value],
         "any(denovo)"),
        ({"neither"},
         {"neither"},
         [Inheritance.unknown.value],
         [],
         "any(denovo,mendelian,missing,omission,unknown)"),
    ])
def test_transform_present_in_child_and_present_in_parent_inheritance(
    present_in_child: set[str],
    present_in_parent: set[str],
    accepted: list[int],
    rejected: list[int],
    expected_query: str,
) -> None:
    inheritance_query = QueryTransformer\
        ._transform_present_in_child_and_parent_inheritance(
            present_in_child, present_in_parent)
    assert inheritance_query is not None
    assert inheritance_query == expected_query
    for value in accepted:
        assert SqlQueryBuilder.check_inheritance_query_value(
            [inheritance_query], value)
    for value in rejected:
        assert not SqlQueryBuilder.check_inheritance_query_value(
            [inheritance_query], value)
