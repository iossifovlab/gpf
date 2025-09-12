# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
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

    kwargs = {
        "presentInChild": QueryTransformer._present_in_child_to_roles(
            present_in_child,
        ),
        "presentInParent": QueryTransformer._present_in_parent_to_roles(
            present_in_parent,
        ),
    }
    roles_q = QueryTransformer._transform_present_in_child_and_parent_roles(
        kwargs,
    )
    assert roles_q is not None
    role_matcher = transform_attribute_query_to_function(Role, roles_q)

    inheritance_q = QueryTransformer\
        ._transform_present_in_child_and_parent_inheritance(
            present_in_child, present_in_parent)
    assert inheritance_q is not None
    inheritance_matcher = transform_attribute_query_to_function(
        Inheritance, inheritance_q)

    roles_value = 0
    for role in roles:
        roles_value |= role.value

    inheritances_value = 0
    for inh in inheritance:
        inheritances_value |= inh.value

    roles_matched = role_matcher(roles_value)
    inheritance_matched = inheritance_matcher(inheritances_value)

    assert (roles_matched and inheritance_matched) == \
        accepted, (roles_matched, inheritance_matched)


def test_attributes_query_roles() -> None:
    roles_q = "sib and not prb"
    role_matcher = transform_attribute_query_to_function(Role, roles_q)

    assert not role_matcher(Role.prb.value)


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
         "((prb and not sib) or (sib and not prb) or (prb and sib)) "
         "and (dad and not mom)"),
    ])
def test_transform_present_in_child_and_present_in_parent_roles(
    present_in_child: set[str],
    present_in_parent: set[str],
    accepted: list[int],
    rejected: list[int],
    expected_query: str,
) -> None:
    kwargs = {
        "presentInChild": QueryTransformer._present_in_child_to_roles(
            present_in_child,
        ),
        "presentInParent": QueryTransformer._present_in_parent_to_roles(
            present_in_parent,
        ),
    }
    roles_query = QueryTransformer._transform_present_in_child_and_parent_roles(
        kwargs,
    )
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
         "any([denovo])"),
        ({"neither"},
         {"neither"},
         [Inheritance.unknown.value],
         [],
         "any([denovo,mendelian,missing,omission,unknown])"),
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


@pytest.mark.parametrize(
    "present_in_parent,zygosity_in_parent,expected_query",
    [
        (
            {"mother only", "neither"},
            "homozygous",
            "(mom~homozygous and not dad~homozygous) or (not mom and not dad)",
        ),
        (
            {"father only", "neither"},
            "homozygous",
            "(dad~homozygous and not mom~homozygous) or (not mom and not dad)",
        ),
        (
            {"mother and father", "neither"},
            "homozygous",
            "(mom~homozygous and dad~homozygous) or (not mom and not dad)",
        ),
        (
            {"neither"},
            "homozygous",
            "not mom and not dad",
        ),
        (
            {"father only", "mother only", "mother and father", "neither"},
            "homozygous",
            "(mom~homozygous and not dad~homozygous) or "
            "(dad~homozygous and not mom~homozygous) or "
            "(mom~homozygous and dad~homozygous) or "
            "(not mom and not dad)",
        ),
        (
            {"mother only", "neither"},
            "heterozygous",
            "(mom~heterozygous and not dad~heterozygous) or "
            "(not mom and not dad)",
        ),
        (
            {"father only", "neither"},
            "heterozygous",
            "(dad~heterozygous and not mom~heterozygous) or "
            "(not mom and not dad)",
        ),
        (
            {"mother and father", "neither"},
            "heterozygous",
            "(mom~heterozygous and dad~heterozygous) or (not mom and not dad)",
        ),
        (
            {"neither"},
            "heterozygous",
            "not mom and not dad",
        ),
        (
            {"father only", "mother only", "mother and father", "neither"},
            "heterozygous",
            "(mom~heterozygous and not dad~heterozygous) or "
            "(dad~heterozygous and not mom~heterozygous) or "
            "(mom~heterozygous and dad~heterozygous) or "
            "(not mom and not dad)",
        ),
    ],
)
def test_transform_parent_zygosity_with_neither(
    present_in_parent: set[str],
    zygosity_in_parent: str | None,
    expected_query: str,
) -> None:
    parents_query = QueryTransformer._present_in_parent_to_roles(
        present_in_parent, zygosity_in_parent)

    assert parents_query == expected_query
