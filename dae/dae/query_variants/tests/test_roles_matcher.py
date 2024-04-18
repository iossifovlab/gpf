# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.query_variants.attributes_query import role_query
from dae.variants.attributes import Role


def test_roles_matcher():
    roles = "dad"

    roles = role_query.transform_tree_to_matcher(
        role_query.transform_query_string_to_tree(roles),
    )
    assert roles.match([Role.dad])
    assert roles.match([Role.dad, Role.mom])
    assert not roles.match([Role.mom])
