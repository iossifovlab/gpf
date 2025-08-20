# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.query_variants.attribute_queries import (
    transform_attribute_query_to_function,
)
from dae.variants.attributes import Role


def test_roles_matcher() -> None:
    roles = "dad"

    matcher = transform_attribute_query_to_function(Role, roles)
    assert matcher(Role.dad.value)
    assert matcher(Role.dad.value | Role.mom.value)
    assert not matcher(Role.mom.value)
