# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.query_variants.attributes_query import (
    OrNode,
    inheritance_query,
    role_query,
)
from dae.variants.attributes import Inheritance, Role
from studies.query_transformer import QueryTransformer


@pytest.mark.parametrize(
    "present_in_child,present_in_parent,inheritance,roles,accepted",
    [
        (
            set(["proband only"]),
            set(["neither"]),
            [Inheritance.denovo], [Role.prb], True),
        (
            set(["proband only"]),
            set(["neither"]),
            [Inheritance.denovo], [Role.sib], False),
        (
            set(["proband only"]),
            set(["neither"]),
            [Inheritance.mendelian], [Role.prb], False),
        (
            set(["proband only", "sibling only"]),
            set(["neither"]),
            [Inheritance.denovo], [Role.prb], True),
        (
            set(["proband only", "sibling only"]),
            set(["neither"]),
            [Inheritance.denovo], [Role.sib], True),
        (
            set(["proband only", "sibling only"]),
            set(["neither"]),
            [Inheritance.denovo], [Role.prb, Role.sib], False),
        (
            set(["proband only", "sibling only", "proband and sibling"]),
            set(["neither"]),
            [Inheritance.denovo], [Role.prb, Role.sib], True),
        (
            set(["proband only"]),
            set(["mother only"]),
            [Inheritance.mendelian], [Role.prb, Role.mom], True),
        (
            set(["proband only"]),
            set(["mother only"]),
            [Inheritance.denovo, Inheritance.mendelian],
            [Role.prb, Role.mom], True),
        (
            set(["neither"]),
            set(["mother only"]),
            [Inheritance.missing],
            [Role.mom], True),
        (
            set(["proband only", "proband and sibling", "neither"]),
            set(["mother only", "neither"]),
            [Inheritance.denovo, Inheritance.mendelian, Inheritance.missing],
            [Role.prb, Role.sib, Role.mom], True),
    ],
)
def test_transform_present_in_child_and_present_in_parent(
        present_in_child: set[str], present_in_parent: set[str],
        inheritance: list[Inheritance],
        roles: list[Role], accepted: bool) -> None:

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
