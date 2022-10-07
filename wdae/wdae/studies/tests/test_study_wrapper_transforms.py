import pytest

from studies.query_transformer import QueryTransformer

from dae.variants.attributes import Inheritance, Role
from dae.query_variants.attributes_query import inheritance_query, \
    role_query, \
    OrNode


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
    ]
)
def test_transform_present_in_child_and_present_in_parent(
        present_in_child, present_in_parent, inheritance, roles, accepted):

    rq = QueryTransformer._transform_present_in_child_and_parent_roles(
        present_in_child, present_in_parent)
    rm = role_query.transform_tree_to_matcher(rq)

    iq = QueryTransformer._transform_present_in_child_and_parent_inheritance(
        present_in_child, present_in_parent)

    assert iq is not None

    print("roles query:      ", rq)
    print("inheritance query:", iq)

    it = inheritance_query.transform_query_string_to_tree(iq)
    im = inheritance_query.transform_tree_to_matcher(it)

    roles_matched = rm.match(roles)
    inheritance_matched = im.match(inheritance)

    assert (rm.match(roles) and im.match(inheritance)) == accepted, (
        roles_matched, inheritance_matched)


def test_attributes_query_roles():
    rq = "sib and not prb"
    rt = OrNode([role_query.transform_query_string_to_tree(rq)])

    rm = role_query.transform_tree_to_matcher(rt)

    result = rm.match([Role.prb])
    assert not result
